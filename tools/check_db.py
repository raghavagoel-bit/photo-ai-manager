import sqlite3
import os
import numpy as np

DB_PATH = os.path.join('photo_manager', 'data', 'index.db')

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as count FROM photos')
    photos_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM faces')
    faces_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM people')
    people_count = c.fetchone()['count']
    
    print(f"Photos in DB: {photos_count}")
    print(f"Faces in DB: {faces_count}")
    print(f"People in DB: {people_count}")
    
    if faces_count > 0:
        c.execute('SELECT * FROM faces LIMIT 5')
        rows = c.fetchall()
        for r in rows:
            encoding = np.frombuffer(r['encoding'], dtype=np.float64)
            norm = np.linalg.norm(encoding)
            print(f"Face ID: {r['id']}, Dim: {len(encoding)}, L2 Norm: {norm:.4f}")
            
    conn.close()

if __name__ == "__main__":
    check_db()
