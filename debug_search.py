import sqlite3
import os

DB_PATH = 'data/index.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Database Snapshot ---")
c.execute("SELECT COUNT(*) FROM photos")
print(f"Total photos: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM photos WHERE ai_tags IS NOT NULL")
print(f"Photos with AI tags: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM photos WHERE location_tags LIKE '%Kenya%'")
print(f"Photos in Kenya: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM photos WHERE location_tags LIKE '%Kenya%' AND ai_tags IS NOT NULL")
print(f"Photos in Kenya WITH AI tags: {c.fetchone()[0]}")

# Check what the AI is finding
c.execute("SELECT ai_tags, COUNT(*) as count FROM photos WHERE ai_tags IS NOT NULL GROUP BY ai_tags ORDER BY count DESC LIMIT 10")
print("\nTop AI Tags found so far:")
for r in c.fetchall():
    print(f"  {r['ai_tags']}: {r['count']}")

# Test the combined query logic
query = "Kenya"
terms = ["Kenya"]
clauses = ["(pe.name LIKE ? OR p.location_tags LIKE ? OR p.file_path LIKE ? OR p.ai_tags LIKE ?)"]
params = ["%Kenya%", "%Kenya%", "%Kenya%", "%Kenya%"]
where_clause = " AND ".join(clauses)

c.execute(f'''
    SELECT COUNT(DISTINCT p.id) as total
    FROM photos p
    LEFT JOIN faces f ON p.id = f.photo_id
    LEFT JOIN people pe ON f.person_id = pe.id
    WHERE {where_clause}
''', params)
print(f"\nResults for 'Kenya': {c.fetchone()[0]}")

# Test "Kenya Lion"
query = "Kenya Lion"
terms = ["Kenya", "Lion"]
clauses = [
    "(pe.name LIKE ? OR p.location_tags LIKE ? OR p.file_path LIKE ? OR p.ai_tags LIKE ?)",
    "(pe.name LIKE ? OR p.location_tags LIKE ? OR p.file_path LIKE ? OR p.ai_tags LIKE ?)"
]
params = ["%Kenya%", "%Kenya%", "%Kenya%", "%Kenya%", "%Lion%", "%Lion%", "%Lion%", "%Lion%"]
where_clause = " AND ".join(clauses)

c.execute(f'''
    SELECT COUNT(DISTINCT p.id) as total
    FROM photos p
    LEFT JOIN faces f ON p.id = f.photo_id
    LEFT JOIN people pe ON f.person_id = pe.id
    WHERE {where_clause}
''', params)
print(f"Results for 'Kenya Lion': {c.fetchone()[0]}")

conn.close()
