import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, get_photo_v3_status
from scanner import scan_directory

def verify():
    # 1. Peek at DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT file_path FROM photos LIMIT 5")
    rows = c.fetchall()
    if not rows:
        print("No photos in DB to hydrate.")
        return
    
    test_paths = [r['file_path'] for r in rows]
    print(f"Checking status for {len(test_paths)} photos...")
    for p in test_paths:
        status = get_photo_v3_status(p)
        print(f"Path: {os.path.basename(p)} | Complete: {status['is_complete']}")

    # 2. Trigger Hydration Scan on the parent directory of one of these photos
    # We'll use the first one's parent
    root_to_scan = os.path.dirname(test_paths[0])
    print(f"\nTriggering hydration scan on: {root_to_scan}")
    
    scanned, faces = scan_directory(root_to_scan)
    print(f"Scan complete: {scanned} hydrated/scanned, {faces} faces found.")

    # 3. Re-verify
    print("\nRe-verifying status...")
    for p in test_paths:
        status = get_photo_v3_status(p)
        print(f"Path: {os.path.basename(p)} | Complete: {status['is_complete']} | pHash: {status['phash'][:16]}...")

if __name__ == "__main__":
    verify()
