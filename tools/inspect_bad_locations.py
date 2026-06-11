import sqlite3
import os
import sys

# Include correct base dir
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from database import get_connection
except ImportError:
    # Direct fallback when run outside the project root
    db_path = os.path.join(parent_dir, 'data', 'index.db')
    def get_connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def inspect():
    conn = get_connection()
    c = conn.cursor()
    
    # Query for photos roughly in US longitude box (negative lon -130 to -60)
    c.execute("""
        SELECT id, file_path, date_taken, latitude, longitude 
        FROM photos 
        WHERE longitude < -60 AND longitude > -130
        LIMIT 10
    """)
    rows = c.fetchall()
    
    print(f"Found {len(rows)} sample photos in suspected USA coordinate range:")
    for r in rows:
        print(f"ID: {r['id']} | Date: {r['date_taken']} | Lat: {r['latitude']} | Lon: {r['longitude']} | Path: {r['file_path']}")
        
    # Count total count
    c.execute("SELECT COUNT(*) FROM photos WHERE longitude < -60 AND longitude > -130")
    print(f"Total photos in US range: {c.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    inspect()
