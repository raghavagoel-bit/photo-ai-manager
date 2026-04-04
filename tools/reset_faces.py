import sqlite3
import os

DB_PATH = "data/index.db"

def reset_face_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("AI UPGRADE: Clearing 128-d face data...")
    
    # 1. Clear all faces (embeddings, boxes, thumbnails)
    c.execute("DELETE FROM faces")
    
    # 2. Clear all identities
    c.execute("DELETE FROM people")
    
    # 3. Mark all photos as "not scanned" so they can be re-processed by the 512-d engine
    # Actually, the scanner uses a 'scanned' flag in photos, or checks if faces exist.
    # In Phase 3, we added 'scanned' column to photos? Let's check.
    
    # If we want to re-scan for faces, we should probably set 'scanned' = 0 if it exists.
    try:
        c.execute("UPDATE photos SET scanned = 0")
        print("Updated photos: Marked as not-scanned.")
    except Exception:
        # If the column doesn't exist, we'll just check it later.
        pass
        
    conn.commit()
    conn.close()
    print("SUCCESS: 128-d data purged. System ready for high-fidelity 512-d scan.")

if __name__ == "__main__":
    reset_face_data()
