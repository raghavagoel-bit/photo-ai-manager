import sqlite3
import os
import json
import numpy as np

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'index.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Return rows as dictionaries for easier FastAPI serialization
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Photos table
    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            location_tags TEXT,
            ai_tags TEXT,
            date_taken TEXT,
            latitude REAL,
            longitude REAL,
            camera_make TEXT,
            camera_model TEXT,
            iso TEXT,
            aperture TEXT,
            focal_length TEXT,
            phash TEXT,
            thumbnail_path TEXT,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # People table
    c.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    # Faces table
    c.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER,
            person_id INTEGER,
            box_top INTEGER,
            box_right INTEGER,
            box_bottom INTEGER,
            box_left INTEGER,
            encoding BLOB,
            thumbnail_path TEXT,
            FOREIGN KEY(photo_id) REFERENCES photos(id),
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    ''')
    
    # SCHEMA MIGRATION (V1 -> V2)
    # Safely add metadata columns for existing V1 databases
    needed_columns = {
        "camera_make": "TEXT",
        "camera_model": "TEXT",
        "iso": "TEXT",
        "aperture": "TEXT",
        "focal_length": "TEXT",
        "latitude": "REAL",
        "longitude": "REAL",
        "phash": "TEXT",
        "thumbnail_path": "TEXT"
    }
    
    c.execute('PRAGMA table_info(photos)')
    existing_cols = [row['name'] for row in c.fetchall()]
    
    for col, col_type in needed_columns.items():
        if col not in existing_cols:
            print(f"[DATABASE] Migrating: Adding missing column {col} to photos table.")
            c.execute(f'ALTER TABLE photos ADD COLUMN {col} {col_type}')
    
    conn.commit()
    conn.close()

def get_photo_v3_status(file_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, phash, thumbnail_path FROM photos WHERE file_path = ?', (file_path,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row['id'],
        "is_complete": bool(row['phash'] and row['thumbnail_path']),
        "phash": row['phash'],
        "thumbnail_path": row['thumbnail_path']
    }

def update_photo_v3_data(photo_id, latitude, longitude, phash, thumbnail_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE photos 
        SET latitude = ?, longitude = ?, phash = ?, thumbnail_path = ?
        WHERE id = ?
    ''', (latitude, longitude, phash, thumbnail_path, photo_id))
    conn.commit()
    conn.close()

def insert_photo(file_path, location_tags, date_taken, ai_tags="", camera_make="", camera_model="", iso="", aperture="", focal_length="", **kwargs):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO photos (file_path, location_tags, date_taken, ai_tags, camera_make, camera_model, iso, aperture, focal_length, latitude, longitude, phash, thumbnail_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, location_tags, date_taken, ai_tags, camera_make, camera_model, iso, aperture, focal_length,
              kwargs.get('latitude'), kwargs.get('longitude'), kwargs.get('phash'), kwargs.get('thumbnail_path')))
        photo_id = c.lastrowid
        if not photo_id:
            c.execute('SELECT id FROM photos WHERE file_path = ?', (file_path,))
            photo_id = c.fetchone()['id']
        conn.commit()
        return photo_id
    finally:
        conn.close()

def update_photo_tags(photo_id, ai_tags):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE photos SET ai_tags = ? WHERE id = ?', (ai_tags, photo_id))
    conn.commit()
    conn.close()
    return photo_id

def insert_face(photo_id, box, encoding_array, thumbnail_path):
    conn = get_connection()
    c = conn.cursor()
    
    box_top, box_right, box_bottom, box_left = box
    encoding_bytes = encoding_array.tobytes()
    
    c.execute('''
        INSERT INTO faces (photo_id, person_id, box_top, box_right, box_bottom, box_left, encoding, thumbnail_path)
        VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
    ''', (photo_id, box_top, box_right, box_bottom, box_left, encoding_bytes, thumbnail_path))
    face_id = c.lastrowid
    conn.commit()
    conn.close()
    return face_id

def get_person_by_name(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM people WHERE name = ?', (name,))
    row = c.fetchone()
    conn.close()
    return row['id'] if row else None

def create_person(name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO people (name) VALUES (?)', (name,))
        person_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        c.execute('SELECT id FROM people WHERE name = ?', (name,))
        person_id = c.fetchone()['id']
    finally:
        conn.close()
    return person_id

def update_face_person(face_id, person_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE faces SET person_id = ? WHERE id = ?', (person_id, face_id))
    conn.commit()
    conn.close()

def untag_face(face_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE faces SET person_id = NULL WHERE id = ?', (face_id,))
    conn.commit()
    conn.close()

def get_all_faces(has_person=None):
    conn = get_connection()
    c = conn.cursor()
    if has_person is True:
        c.execute('SELECT * FROM faces WHERE person_id IS NOT NULL')
    elif has_person is False:
        c.execute('SELECT * FROM faces WHERE person_id IS NULL')
    else:
        c.execute('SELECT * FROM faces')
    
    rows = c.fetchall()
    conn.close()
    
    faces = []
    for r in rows:
        face = dict(r)
        # deserialize numpy array
        face['encoding'] = np.frombuffer(face['encoding'], dtype=np.float64)
        faces.append(face)
    return faces

def get_duplicate_clusters():
    conn = get_connection()
    c = conn.cursor()
    # Group photos by phash, but only where phash is not null/empty and count > 1
    c.execute('''
        SELECT phash, GROUP_CONCAT(id) as photo_ids 
        FROM photos 
        WHERE phash IS NOT NULL AND phash != '' 
        GROUP BY phash 
        HAVING COUNT(id) > 1
    ''')
    rows = c.fetchall()
    
    clusters = []
    for r in rows:
        photo_ids = [int(pid) for pid in r['photo_ids'].split(',')]
        
        # Fetch the actual photo details for these IDs
        placeholders = ','.join(['?'] * len(photo_ids))
        c.execute(f'SELECT id, file_path, date_taken, thumbnail_path FROM photos WHERE id IN ({placeholders})', photo_ids)
        photos_in_cluster = [dict(p) for p in c.fetchall()]
        
        clusters.append({
            'phash': r['phash'],
            'photos': photos_in_cluster
        })
        
    conn.close()
    return clusters

# Initialize DB when the module is imported
init_db()
