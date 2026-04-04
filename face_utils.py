import os
import uuid
import numpy as np
import cv2
from PIL import Image
from deepface import DeepFace

# Known healthy byte counts for weight files (approximate for 512d)
# DeepFace downloads 'facenet512_weights.h5' which is roughly 92,190,816 bytes
FACENET_512_SIZE = 92190816    
RETINAFACE_SIZE = 118667368 

def check_models_health():
    weights_dir = os.path.join(os.path.expanduser("~"), ".deepface", "weights")
    facenet_path = os.path.join(weights_dir, "facenet512_weights.h5")
    retinaface_path = os.path.join(weights_dir, "retinaface.h5")
    
    status = {
        "facenet512": {"exists": False, "size_ok": False, "path": facenet_path},
        "retinaface": {"exists": False, "size_ok": False, "path": retinaface_path},
        "all_ok": False
    }
    
    if os.path.exists(facenet_path):
        status["facenet512"]["exists"] = True
        # For new 512 model, we'll allow slightly more variance or just existence for now 
        # until the user downloads it once and we confirm the exact byte count.
        status["facenet512"]["size_ok"] = (os.path.getsize(facenet_path) >= 90000000)
        
    if os.path.exists(retinaface_path):
        status["retinaface"]["exists"] = True
        status["retinaface"]["size_ok"] = (os.path.getsize(retinaface_path) == RETINAFACE_SIZE)
        
    # A model is only 'bad' if it exists but has the wrong size (corruption)
    # If it doesn't exist yet, it's fine — DeepFace will download it on first scan.
    facenet_bad = status["facenet512"]["exists"] and not status["facenet512"]["size_ok"]
    retinaface_bad = status["retinaface"]["exists"] and not status["retinaface"]["size_ok"]
    
    status["all_ok"] = not (facenet_bad or retinaface_bad)
    return status

def process_image(image_path, thumbnail_dir):
    scale = 1.0
    try:
        # Load image via cv2 to allow pre-scaling for performance/reliability
        # RetinaFace struggles to detect faces in very large (e.g., 4K/8MB) images
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            print(f"AI ENGINE ALERT: Invalid image file {os.path.basename(image_path)}")
            return []
            
        max_dim = 1280.0
        h, w = img_bgr.shape[:2]
        
        # If the image is larger than 1280px on its longest side, scale it down
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_bgr = cv2.resize(img_bgr, (new_w, new_h))

        # Use RetinaFace for detection and Facenet512 for high-fidelity encoding
        # Facenet512 provides 4x more data points than the standard Facenet
        representations = DeepFace.represent(
            img_path=img_bgr,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=True
        )
    except ValueError as ve:
        # DeepFace raises ValueError if no face is found OR if there's a model issue.
        # We check the message to distinguish.
        msg = str(ve).lower()
        if "face could not be detected" in msg:
            print(f"AI: No face in {os.path.basename(image_path)}")
        else:
            print(f"AI ENGINE ALERT (ValueError) in {os.path.basename(image_path)}: {ve}")
        return []
    except Exception as e:
        import traceback
        print(f"AI ENGINE CRITICAL ERROR in {os.path.basename(image_path)}:")
        traceback.print_exc()
        return []
        
    try:
        img = Image.open(image_path).convert('RGB')
    except Exception:
        return []

    faces = []
    for face in representations:
        # DeepFace returns facial_area as x, y, w, h
        area = face.get("facial_area", {})
        if not area:
            continue
            
        x = area.get("x", 0)
        y = area.get("y", 0)
        w = area.get("w", 0)
        h = area.get("h", 0)
        
        # Guard against invalid negative coordinates mapping from DeepFace bounding box
        # Scale back to original dimensions since we downsampled earlier
        left = max(0, int(x / scale))
        top = max(0, int(y / scale))
        right = min(img.width, int((x + w) / scale))
        bottom = min(img.height, int((y + h) / scale))

        # Convert float list to numpy array and perform L2 normalization
        # This ensuring Euclidean distance 0.7-1.0 matches the Facenet standard
        encoding = np.array(face["embedding"], dtype=np.float64)
        norm = np.linalg.norm(encoding)
        if norm > 1e-6:
            encoding = encoding / norm

        # Create 150x150 thumbnail locally so we never load the 4K image in the web browser
        try:
            face_img = img.crop((left, top, right, bottom))
            face_img.thumbnail((150, 150))
            thumb_filename = f"{uuid.uuid4().hex}.jpg"
            thumb_path = os.path.join(thumbnail_dir, thumb_filename)
            face_img.save(thumb_path, "JPEG")
            
            # Pack it matching exactly our Phase 1 Tuple structure (top, right, bottom, left)
            faces.append({
                'box': (top, right, bottom, left),
                'encoding': encoding,
                'thumbnail': thumb_filename
            })
        except Exception as e:
            print(f"Error saving thumbnail for {image_path}: {e}")
            
    if not faces:
        print(f"AI: No faces detected in {image_path} (RetinaFace returned empty or invalid).")
            
    return faces
