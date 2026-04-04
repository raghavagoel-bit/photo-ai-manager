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
            date_taken TEXT
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
    conn.commit()
    conn.close()

def insert_photo(file_path, location_tags="", date_taken=""):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO photos (file_path, location_tags, date_taken)
            VALUES (?, ?, ?)
        ''', (file_path, location_tags, date_taken))
        photo_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        # Already exists, just return its ID
        c.execute('SELECT id FROM photos WHERE file_path = ?', (file_path,))
        photo_id = c.fetchone()['id']
    finally:
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

# Initialize DB when the module is imported
init_db()
