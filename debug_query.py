import sqlite3
import os

DB_PATH = 'data/index.db'
query = "kenya"
search_term = f"%{query}%"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check total photos
c.execute("SELECT COUNT(*) FROM photos")
print(f"Total photos: {c.fetchone()[0]}")

# Check kenya photos
c.execute("SELECT id, location_tags, date_taken FROM photos WHERE location_tags LIKE ?", (search_term,))
kenya_photos = c.fetchall()
print(f"Found {len(kenya_photos)} photos with 'kenya' tag via simple query.")

for p in kenya_photos[:5]:
    print(f"ID: {p['id']}, Tags: {p['location_tags']}, Date: {p['date_taken']}")

# Check complex query
c.execute('''
    SELECT DISTINCT p.id, p.file_path, p.location_tags, p.date_taken
    FROM photos p
    LEFT JOIN faces f ON p.id = f.photo_id
    LEFT JOIN people pe ON f.person_id = pe.id
    WHERE pe.name LIKE ? OR p.location_tags LIKE ? OR p.file_path LIKE ?
''', (search_term, search_term, search_term))
complex_results = c.fetchall()
print(f"Found {len(complex_results)} results via complex query.")

conn.close()
