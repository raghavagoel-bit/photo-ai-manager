import os
import json
import requests
import base64
from io import BytesIO
from PIL import Image

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Assuming standard Ollama naming for Llama 3.2 Vision
MODEL_NAME = "llama3.2-vision"

def encode_and_downsample_image(image_path, max_size=1280):
    """Resizes and compresses image to prevent OOM errors on local LLM."""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed (e.g., from RGBA or Paletted)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Downsample preserving aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Compress to JPEG in memory
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            
            # Base64 encode
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"[LLM] Error downsampling {image_path}: {e}")
        return None

def deduce_location_from_images(image_paths, country_hint="Unknown"):
    """Sends 3-5 images to Ollama Vision LLM to deduce a precise location."""
    images_b64 = []
    for path in image_paths:
        b64 = encode_and_downsample_image(path)
        if b64:
            images_b64.append(b64)
            
    if not images_b64:
        return None
        
    prompt = (
        f"You are a forensic geographic analyst. I am providing you with {len(images_b64)} photos taken in or near {country_hint}. "
        "Analyze these photos carefully for any text (street signs, storefronts, menus), architectural styles, "
        "license plates, or distinct environmental features. "
        "Deduce the specific city, town, or region where these photos were taken. "
        "You must respond ONLY with a valid JSON object in the exact following format:\n"
        "{\n"
        '  "city_or_region": "Name of the deduced city/region",\n'
        '  "confidence": "high" or "low",\n'
        '  "reasoning": "Brief explanation of what you saw that led to this conclusion"\n'
        "}\n"
        "If you cannot deduce a specific location, set confidence to 'low'."
    )
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": images_b64,
        "stream": False,
        "format": "json"
    }
    
    try:
        print(f"   [LLM] Querying Ollama {MODEL_NAME} with {len(images_b64)} sample images (downsampled)...")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        result_text = response.json().get('response', '{}').strip()
        
        # Sometimes LLMs wrap json in markdown code blocks
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "", 1).strip()
            if result_text.endswith("```"):
                result_text = result_text[:-3].strip()
                
        return json.loads(result_text)
    except Exception as e:
        print(f"   [LLM] Inference Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = deduce_location_from_images(sys.argv[1:])
        print(json.dumps(res, indent=2))
