import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import os

_model = None
_device = None
_preprocess = None
_categories = None

def _load_model():
    global _model, _device, _preprocess, _categories
    if _model is not None:
        return
    weights = models.MobileNet_V3_Large_Weights.DEFAULT
    _model = models.mobilenet_v3_large(weights=weights)
    _model.eval()
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model.to(_device)
    _preprocess = weights.transforms()
    _categories = weights.meta["categories"]

def detect_scene(image_path, threshold=0.5):
    """
    Analyzes an image and returns a comma-separated string of recognized objects.
    Only returns objects with confidence above the threshold.
    """
    _load_model()
    try:
        img = Image.open(image_path).convert('RGB')
        img_t = _preprocess(img).unsqueeze(0).to(_device)

        with torch.no_grad():
            output = _model(img_t)

        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        found_tags = []
        for i in range(top5_prob.size(0)):
            prob = top5_prob[i].item()
            if prob >= threshold:
                category = _categories[top5_catid[i]]
                clean_tag = category.split(',')[0].strip()
                found_tags.append(clean_tag)

        return ", ".join(found_tags) if found_tags else ""
    except Exception as e:
        print(f"Scene detection error on {image_path}: {e}")
        return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        tags = detect_scene(sys.argv[1])
        print(f"Tags found: {tags}")
