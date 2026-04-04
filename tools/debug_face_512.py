import os
import cv2
from deepface import DeepFace
import traceback

# Find a real high-res photo from the data dir or current dir
TEST_IMAGE = None
for root, dirs, files in os.walk("."):
    for f in files:
        if f.lower().endswith((".jpg", ".jpeg")) and os.path.getsize(os.path.join(root, f)) > 1024*1024:
            TEST_IMAGE = os.path.join(root, f)
            break
    if TEST_IMAGE: break

if not TEST_IMAGE:
    print("No high-res test image found!")
    exit()

print(f"DEBUGGING: {TEST_IMAGE} ({os.path.getsize(TEST_IMAGE)//1024} KB)")

detectors = ["retinaface", "opencv", "mtcnn"]

for det in detectors:
    print(f"\n--- Testing Detector: {det} ---")
    try:
        # We try to detect faces
        res = DeepFace.represent(
            img_path=TEST_IMAGE,
            model_name="Facenet512",
            detector_backend=det,
            enforce_detection=True
        )
        print(f"SUCCESS: {det} found {len(res)} face(s).")
    except Exception as e:
        print(f"FAILED: {det} reported: {str(e)}")

print("\n--- Testing Pre-scaling (1024px) ---")
try:
    img = cv2.imread(TEST_IMAGE)
    scale = 1024 / max(img.shape[:2])
    small_img = cv2.resize(img, (0,0), fx=scale, fy=scale)
    temp_path = "debug_small.jpg"
    cv2.imwrite(temp_path, small_img)
    
    res = DeepFace.represent(
        img_path=temp_path,
        model_name="Facenet512",
        detector_backend="retinaface",
        enforce_detection=True
    )
    print(f"SUCCESS: Pre-scaled RetinaFace found {len(res)} face(s).")
    os.remove(temp_path)
except Exception as e:
    print(f"FAILED: Pre-scaled test reported: {str(e)}")
