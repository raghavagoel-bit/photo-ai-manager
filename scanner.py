import os
import exifread
from main_backend import get_connection
from face_utils import process_image
from scene_utils import detect_scene

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png'}
THUMBNAIL_DIR = os.path.join(os.path.dirname(__file__), 'data', 'thumbnails')

def get_exif_location(image_path):
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
        date_taken = str(tags.get('EXIF DateTimeOriginal', ''))
        dir_name = os.path.basename(os.path.dirname(image_path))
        return dir_name, date_taken
    except Exception:
        return os.path.basename(os.path.dirname(image_path)), ""

def is_scanned(file_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM photos WHERE file_path = ?', (file_path,))
    row = c.fetchone()
    conn.close()
    return row is not None

def scan_directory(root_dir, status_dict=None):
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    scanned_count = 0
    face_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTS:
                full_path = os.path.join(root, file)
                
                if is_scanned(full_path):
                    continue
                
                loc_tags, date_taken = get_exif_location(full_path)
                
                # Dual AI: Face Recognition + Scene Awareness
                print(f"Scanning [{scanned_count+1}]: {file} ({os.path.getsize(full_path)//1024//1024}MB)...")
                
                faces = process_image(full_path, THUMBNAIL_DIR)
                ai_tags = detect_scene(full_path) # Identify Animals, Objects, Places
                
                if faces:
                    photo_id = insert_photo(full_path, loc_tags, date_taken, ai_tags)
                    for face in faces:
                        insert_face(photo_id, face['box'], face['encoding'], face['thumbnail'])
                        face_count += 1
                else:
                    insert_photo(full_path, loc_tags, date_taken, ai_tags)
                    
                scanned_count += 1
                if status_dict is not None:
                    status_dict["scanned_count"] = scanned_count
                    status_dict["face_count"] = face_count
                
    return scanned_count, face_count
