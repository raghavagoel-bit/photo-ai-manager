import os
import exifread
import imagehash
from PIL import Image
from database import get_connection, insert_photo, insert_face, get_photo_v3_status, update_photo_v3_data
from face_utils import process_image, ensure_models_loaded, generate_thumbnails

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png'}
THUMBNAIL_DIR = os.path.join(os.path.dirname(__file__), 'data', 'thumbnails')

def get_gps_decimal(tags):
    """Helper to convert raw EXIF GPS tags to fractional decimal."""
    def _to_float(ref, val):
        if not val or not ref: return None
        # EXIF format is usually [deg, min, sec]
        d, m, s = [float(x.num) / float(x.den) for x in val.values]
        decimal = d + (m / 60.0) + (s / 3600.0)
        if ref.values in ['S', 'W']:
            decimal = -decimal
        return decimal

    try:
        lat = _to_float(tags.get('GPS GPSLatitudeRef'), tags.get('GPS GPSLatitude'))
        lon = _to_float(tags.get('GPS GPSLongitudeRef'), tags.get('GPS GPSLongitude'))
        return lat, lon
    except Exception:
        return None, None

def get_exif_data(image_path):
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
        date_taken = str(tags.get('EXIF DateTimeOriginal', ''))
        make = str(tags.get('Image Make', ''))
        model = str(tags.get('Image Model', ''))
        iso = str(tags.get('EXIF ISOSpeedRatings', ''))
        aperture = str(tags.get('EXIF FNumber', ''))
        focal = str(tags.get('EXIF FocalLength', ''))
        
        # Precise GPS
        lat, lon = get_gps_decimal(tags)
        
        # Simple Location Tag (Folder Name)
        dir_name = os.path.basename(os.path.dirname(image_path))
        loc_tags = dir_name
        
        return loc_tags, date_taken, make, model, iso, aperture, focal, lat, lon
    except Exception:
        return os.path.basename(os.path.dirname(image_path)), "", "", "", "", "", "", None, None

# is_scanned is deprecated in favor of get_photo_v3_status

def scan_directory(root_dir, status_dict=None):
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    if status_dict is not None:
        status_dict["phase"] = "Initializing AI Models (RetinaFace + FaceNet512)..."
    
    ensure_models_loaded()
    
    if status_dict is not None:
        status_dict["phase"] = "Walking Directory Tree..."
        
    scanned_count = 0
    face_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTS:
                full_path = os.path.join(root, file)
                
                if status_dict is not None:
                    status_dict["phase"] = f"Analyzing: {file}"
                
                v3_status = get_photo_v3_status(full_path)
                if v3_status and v3_status["is_complete"]:
                    continue
                
                # Dual AI: Face Recognition + Scene Awareness
                action = "Hydrating" if v3_status else "Scanning"
                print(f"{action} [{scanned_count+1}]: {file} ({os.path.getsize(full_path)//1024//1024}MB)...")

                loc_tags, date_taken, make, model, iso, aperture, focal, lat, lon = get_exif_data(full_path)
                
                # 1. Image Hashing (Duplicate Detection) + 2. Tiered Thumbnails
                try:
                    with Image.open(full_path) as img_pil:
                        phash = str(imagehash.phash(img_pil))
                        photo_thumb = generate_thumbnails(img_pil, THUMBNAIL_DIR)
                except Exception as e:
                    print(f"Hashing/Thumb error on {file}: {e}")
                    phash = ""
                    photo_thumb = ""

                if v3_status:
                    # Maintenance Hydration (Backfilling V3 columns)
                    update_photo_v3_data(v3_status['id'], lat, lon, phash, photo_thumb)
                else:
                    # Fresh Scan
                    faces = process_image(full_path, THUMBNAIL_DIR)
                    from scene_utils import detect_scene
                    ai_tags = detect_scene(full_path) 
                    
                    photo_id = insert_photo(full_path, loc_tags, date_taken, ai_tags, make, model, iso, aperture, focal, 
                                            latitude=lat, longitude=lon, phash=phash, thumbnail_path=photo_thumb)
                    
                    if faces:
                        for face in faces:
                            insert_face(photo_id, face['box'], face['encoding'], face['thumbnail'])
                            face_count += 1
                    
                scanned_count += 1
                if status_dict is not None:
                    status_dict["scanned_count"] = scanned_count
                    status_dict["face_count"] = face_count
                
    if status_dict is not None:
        status_dict["phase"] = "Scan Complete"
        
    return scanned_count, face_count
