import sqlite3
import os

DB_PATH = os.path.join("data", "index.db")

def audit():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM photos")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM photos WHERE latitude IS NOT NULL")
    with_gps = c.fetchone()[0]
    
    c.execute("SELECT DISTINCT location_tags FROM photos")
    loc_tags = [str(r[0]) for r in c.fetchall() if r[0]]
    
    c.execute("SELECT COUNT(*) FROM faces")
    faces = c.fetchone()[0]
    
    print(f"Total Photos: {total}")
    print(f"Photos with GPS: {with_gps} ({round(with_gps/total*100, 1)}%)")
    print(f"Unique Location Tags: {len(loc_tags)}")
    print(f"Top Location Tags: {loc_tags[:10]}")
    print(f"Total Faces: {faces}")
    
    conn.close()

if __name__ == "__main__":
    audit()
