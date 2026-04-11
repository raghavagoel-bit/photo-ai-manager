import sqlite3
import os

DB_PATH = os.path.join("data", "index.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- PHOTOS IN ITALY ---")
c.execute("SELECT id, file_path, latitude, longitude, location_tags FROM photos WHERE file_path LIKE '%Italy%' LIMIT 20")
for row in c.fetchall():
    print(dict(row))

print("\n--- SCHEMA ---")
c.execute("PRAGMA table_info(photos)")
for row in c.fetchall():
    print(dict(row))

conn.close()
