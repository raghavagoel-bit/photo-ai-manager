import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import os

# Initialize MobileNetV3-Large (High accuracy, low latency)
# We use the default weights (ImageNet-1K)
weights = models.MobileNet_V3_Large_Weights.DEFAULT
model = models.mobilenet_v3_large(weights=weights)
model.eval()

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Image preprocessing pipeline (matches ImageNet standards)
preprocess = weights.transforms()

# Get human-readable categories
categories = weights.meta["categories"]

def detect_scene(image_path, threshold=0.5):
    """
    Analyzes an image and returns a comma-separated string of recognized objects.
    Only returns objects with confidence above the threshold.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        # Quick resize for speed during 1TB scans
        img_t = preprocess(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = model(img_t)
        
        # Convert output to probabilities
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        
        # Get top predictions
        top5_prob, top5_catid = torch.topk(probabilities, 5)
        
        found_tags = []
        for i in range(top5_prob.size(0)):
            prob = top5_prob[i].item()
            if prob >= threshold:
                category = categories[top5_catid[i]]
                # Clean up labels (e.g., 'German shepherd, German shepherd dog' -> 'German shepherd')
                clean_tag = category.split(',')[0].strip()
                found_tags.append(clean_tag)
                
        return ", ".join(found_tags) if found_tags else ""
    except Exception as e:
        print(f"Scene detection error on {image_path}: {e}")
        return ""

if __name__ == "__main__":
    # Test with a photo if provided
    import sys
    if len(sys.argv) > 1:
        tags = detect_scene(sys.argv[1])
        print(f"Tags found: {tags}")
