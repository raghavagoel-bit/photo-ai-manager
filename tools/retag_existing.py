import os
import sys

# Add project root to path so we can import from database and scene_utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import get_connection, update_photo_tags
from scene_utils import detect_scene

def retag_all():
    print("Starting AI Scene Backfill for your existing library...")
    
    conn = get_connection()
    c = conn.cursor()
    
    # Find all photos that don't have AI tags yet
    c.execute("SELECT id, file_path FROM photos WHERE ai_tags IS NULL OR ai_tags = ''")
    to_tag = c.fetchall()
    conn.close()
    
    total = len(to_tag)
    print(f"Found {total} photos to analyze.")
    
    if total == 0:
        print("✅ All photos are already tagged!")
        return

    processed = 0
    for row in to_tag:
        photo_id = row['id']
        file_path = row['file_path']
        
        if not os.path.exists(file_path):
            print(f"Skipping missing file: {file_path}")
            continue
            
        print(f"Analyzing [{processed+1}/{total}]: {os.path.basename(file_path)}...")
        
        # Run AI detection
        tags = detect_scene(file_path)
        
        if tags:
            update_photo_tags(photo_id, tags)
            print(f"  - Tags: {tags}")
        else:
            # Mark as empty so we don't try again
            update_photo_tags(photo_id, "none")
            
        processed += 1

    print(f"Successfully retagged {processed} photos!")

if __name__ == "__main__":
    retag_all()
