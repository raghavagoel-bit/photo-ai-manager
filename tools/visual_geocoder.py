import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import json
import os

# Initialize CLIP Model Globally
MODEL_ID = "openai/clip-vit-base-patch32"
# Force CPU due to RTX 5070 CUDA kernel compatibility issues
device = torch.device("cpu")

print(f"[V3.3-AI] Initializing CLIP Geocoder on {device}...")
model = CLIPModel.from_pretrained(MODEL_ID).to(device)
processor = CLIPProcessor.from_pretrained(MODEL_ID)

# Load Anchors
ANCHORS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "anchors.json")
with open(ANCHORS_PATH, 'r') as f:
    ANCHORS_DATA = json.load(f)

def identify_location(image_path, country, threshold=0.75):
    """
    Identifies a specific location anchor within a country using CLIP.
    Returns: (name, lat, lon, confidence) or None
    """
    if country not in ANCHORS_DATA:
        return None

    try:
        image = Image.open(image_path).convert("RGB")
        anchors = ANCHORS_DATA[country]
        candidate_names = [a['name'] for a in anchors]
        
        # Prepare inputs
        inputs = processor(text=candidate_names, images=image, return_tensors="pt", padding=True).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image  # image-text similarity score
            probs = logits_per_image.softmax(dim=1)      # label probabilities

        # Get best match
        max_prob, idx = torch.max(probs[0], dim=0)
        confidence = max_prob.item()

        if confidence >= threshold:
            best_anchor = anchors[idx]
            return (best_anchor['name'], best_anchor['coords'][0], best_anchor['coords'][1], confidence)
        
        return None

    except Exception as e:
        print(f"[V3.3-ERROR] Visual Geocoding failed for {image_path}: {e}")
        return None

if __name__ == "__main__":
    # Test script
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        cntry = sys.argv[2]
        result = identify_location(img, cntry)
        if result:
            print(f"Match Found: {result[0]} ({result[3]:.2f}) at {result[1]}, {result[2]}")
        else:
            print("No high-confidence match found.")
