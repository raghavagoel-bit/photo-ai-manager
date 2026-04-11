import sqlite3
import os

DB_PATH = os.path.join("data", "index.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- RECENTLY UPGRADED LANDMARKS ---")
c.execute("SELECT id, file_path, latitude, longitude, location_tags FROM photos WHERE location_tags LIKE '%Colosseum%' OR location_tags LIKE '%Venice%' OR location_tags LIKE '%Taj Mahal%' LIMIT 20")
rows = c.fetchall()
if not rows:
    print("No precision anchors found yet.")
else:
    for row in rows:
        print(dict(row))

conn.close()
