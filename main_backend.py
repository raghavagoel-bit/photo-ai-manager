from fastapi import FastAPI, BackgroundTasks, Request, Depends, Form
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import psutil
from database import (get_all_faces, update_face_person, untag_face,
                     create_person, get_person_by_name, get_connection, insert_face, insert_photo, update_photo_v3_data)
from scanner import scan_directory
from face_utils import check_models_health, match_face, compute_person_centroids

# App version for health checks
APP_VERSION = "1.6.1-cartography-v3.3"
app = FastAPI()

# Mount static folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/thumbnails", StaticFiles(directory="data/thumbnails"), name="thumbnails")

templates = Jinja2Templates(directory="templates")

# Global variables for background task state
scan_status = {"is_scanning": False, "scanned_count": 0, "face_count": 0, "phase": "Idle"}

@app.on_event("startup")
async def startup_event():
    print("\n--- AI Engine Health Check ---")
    status = check_models_health()
    if status["all_ok"]:
        print("[OK] Models found and verified (Facenet512 + RetinaFace)")
    else:
        print("[ALERT] AI ENGINE ALERT: Models missing or corrupt!")
        if not status["facenet512"]["size_ok"]: print(f"   - Facenet512: {status['facenet512']['path']} is invalid")
        if not status["retinaface"]["size_ok"]: print(f"   - RetinaFace: {status['retinaface']['path']} is invalid")
        print("   Please ensure models are downloaded correctly before scanning.")
    print("------------------------------\n")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/health")
async def health_check():
    """System health check and version verification."""
    try:
        conn = get_connection()
        conn.close()
        return {
            "status": "ok",
            "version": APP_VERSION,
            "engine": "Facenet512",
            "scene_ai": "MobileNetV3",
            "db_connected": True
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_scan_task(path: str):
    global scan_status
    scan_status["is_scanning"] = True
    scan_status["scanned_count"] = 0
    scan_status["face_count"] = 0
    scan_status["phase"] = "Ready"
    try:
        scanned, faces = scan_directory(path, status_dict=scan_status)
        scan_status["scanned_count"] = scanned
        scan_status["face_count"] = faces
    finally:
        scan_status["is_scanning"] = False

@app.post("/api/scan")
async def start_scan(background_tasks: BackgroundTasks, path: str = Form(...)):
    global scan_status
    
    # Block scan if models are unhealthy
    health = check_models_health()
    if not health["all_ok"]:
        return {"status": "error", "message": "AI Models (Facenet/RetinaFace) are missing or corrupt. Cannot start scan."}

    if scan_status["is_scanning"]:
        return {"status": "error", "message": "Already scanning"}
    
    if not os.path.exists(path):
        return {"status": "error", "message": "Path does not exist"}
        
    background_tasks.add_task(run_scan_task, path)
    return {"status": "success", "message": "Scanning started in background"}

@app.get("/api/scan/status")
async def get_scan_status():
    return scan_status

@app.get("/api/telemetry")
async def get_telemetry():
    """V2 High-Density Telemetry Endpoint."""
    cpu_usage = psutil.cpu_percent(interval=None)
    ram_usage = psutil.virtual_memory().percent
    
    # AI Score (Placeholder simulation for health/confidence average)
    ai_score = 0.98 if check_models_health()["all_ok"] else 0.0
    
    # Get total photos from DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM photos")
    total_photos = c.fetchone()['total']
    conn.close()
    
    return {
        "is_scanning": scan_status["is_scanning"],
        "phase": scan_status["phase"],
        "scanned_count": scan_status["scanned_count"],
        "total_photos": total_photos,
        "face_count": scan_status["face_count"],
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "ai_score": ai_score,
        "tasks_per_second": round(scan_status["scanned_count"] / max(1, os.times()[4]), 2) if scan_status["is_scanning"] else 0
    }

@app.get("/api/tags/top")
async def get_top_tags(limit: int = 15):
    """Aggregate top AI and Location tags for the Tactical Cloud."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT ai_tags, location_tags FROM photos")
    rows = c.fetchall()
    conn.close()
    
    noise = {'JPEG', 'JPG', 'none', 'None', '', 'none,', 'jpg', 'jpeg'}
    geo_counts = {}
    ai_counts = {}
    
    for r in rows:
        ai = str(r['ai_tags'] or "").lower()
        loc = str(r['location_tags'] or "").lower()
        
        # Split location tags (High Priority)
        loc_parts = [p.strip() for p in loc.replace(',', ' ').split() if p.strip()]
        for p in loc_parts:
            if p not in noise and len(p) > 2:
                name = p.capitalize()
                geo_counts[name] = geo_counts.get(name, 0) + 1
        
        # Split AI tags (Standard Priority)
        ai_parts = [p.strip() for p in ai.replace(',', ' ').split() if p.strip()]
        for p in ai_parts:
            if p not in noise and len(p) > 2:
                name = p.capitalize()
                ai_counts[name] = ai_counts.get(name, 0) + 1
    
    # Prioritize Geography tags in the top manifest
    # Take top 10 Geo, top 5 AI
    top_geo = sorted(geo_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_ai = sorted(ai_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    combined = top_geo + top_ai
    # Deduplicate and re-sort
    final_counts = {}
    for t, c in combined:
        if t not in final_counts: final_counts[t] = c
        
    sorted_tags = sorted(final_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"tag": t, "count": c} for t, c in sorted_tags]

@app.get("/api/identities")
async def get_identities():
    """List all identified persons and a sample image from their cluster."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT pe.id, pe.name, COUNT(f.id) as face_count, MIN(f.thumbnail_path) as sample_thumbnail
        FROM people pe
        JOIN faces f ON pe.id = f.person_id
        GROUP BY pe.id
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/identity/{person_id}/clusters")
async def get_identity_clusters(person_id: int):
    """Retrieve all face crops for a specific person for review."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, thumbnail_path, photo_id
        FROM faces
        WHERE person_id = ?
    ''', (person_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/faces")
async def get_faces(status: str = "all", cluster: bool = False):
    # status: "unknown", "known", "all"
    has_person = None
    if status == "unknown":
        has_person = False
    elif status == "known":
        has_person = True
        
    faces = get_all_faces(has_person=has_person)
    
    if cluster and has_person is False and len(faces) > 0:
        # --- PHASE 7: AUTO-RECOGNITION Pass ---
        # Before clustering unknowns into new groups, check if any match already-named people.
        known_faces = get_all_faces(has_person=True)
        centroids = compute_person_centroids(known_faces) if known_faces else {}
        
        remaining_unknowns = []
        auto_tagged_count = 0
        
        for face in faces:
            # Try to match against existing names (threshold=0.85 is conservative for 512-d)
            matched_person_id = match_face(face['encoding'], centroids, threshold=0.85)
            
            if matched_person_id:
                # We found a known person! Auto-tag them and skip clustering.
                update_face_person(face['id'], matched_person_id)
                auto_tagged_count += 1
            else:
                remaining_unknowns.append(face)
        
        if auto_tagged_count > 0:
            print(f"AI: Auto-recognized {auto_tagged_count} face(s) from previous name mappings.")
            
        # Only cluster the faces that we couldn't automatically recognize.
        if not remaining_unknowns:
            return []
            
        faces = remaining_unknowns
        
        # --- PHASE 4b/6: AgglomerativeClustering on remaining unknowns ---
        encodings = np.stack([f['encoding'] for f in faces])
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1.0,
            metric='euclidean',
            linkage='complete'
        ).fit(encodings)
        labels = clustering.labels_
        
        from sklearn.metrics.pairwise import euclidean_distances
        dist_matrix = euclidean_distances(encodings)
        
        clustered_data = {}
        threshold = 1.0
        for i, label in enumerate(labels):
            face_id = faces[i]['id']
            if label not in clustered_data:
                clustered_data[label] = {
                    "id": face_id,
                    "thumbnail": faces[i]["thumbnail_path"],
                    "clone_ids": [],
                    "indices": []
                }
            clustered_data[label]["clone_ids"].append(face_id)
            clustered_data[label]["indices"].append(i)
            
        # Post-process confidence scores (purity)
        results = []
        for label, data in clustered_data.items():
            indices = data.pop("indices")
            if len(indices) <= 1:
                data["confidence"] = 1.0
            else:
                # Calculate cluster diameter (max distance between any two points in cluster)
                cluster_dists = dist_matrix[np.ix_(indices, indices)]
                diameter = np.max(cluster_dists)
                # Confidence is 1.0 if diameter=0, down to 0 if diameter=threshold
                data["confidence"] = max(0.0, 1.0 - (diameter / (threshold * 1.2))) # Scale 1.2 for safety
            
            results.append(data)
            
        return results

    # Filter out encoding array so it doesn't break JSON
    return [{"id": f["id"], "photo_id": f["photo_id"], "thumbnail": f["thumbnail_path"], "person_id": f["person_id"]} for f in faces]

@app.post("/api/faces/{face_id}/tag")
async def tag_face(face_id: int, person_name: str = Form(...)):
    if not person_name.strip():
        return {"error": "Name cannot be empty"}
        
    person_id = create_person(person_name.strip())
    update_face_person(face_id, person_id)
    return {"status": "success", "person_id": person_id}

@app.post("/api/faces/{face_id}/untag")
async def untag_face_api(face_id: int):
    """Remove a face from its currently assigned identity (Accuracy Management)."""
    untag_face(face_id)
    return {"status": "success"}

@app.post("/api/faces/bulk_tag")
async def bulk_tag_faces(face_ids: str = Form(...), person_name: str = Form(...)):
    # Accepts a comma-separated list of face IDs to massively apply the same tag
    if not person_name.strip():
        return {"error": "Name cannot be empty"}
        
    person_id = create_person(person_name.strip())
    
    ids_to_tag = [int(i.strip()) for i in face_ids.split(",") if i.strip().isdigit()]
    for fid in ids_to_tag:
        update_face_person(fid, person_id)
        
    return {"status": "success", "person_id": person_id, "tagged_count": len(ids_to_tag)}

# --- V3 INTELLIGENCE ENDPOINTS ---

@app.get("/api/atlas")
async def get_atlas_data():
    """Retrieve GPS data for Atlas view, including Temporal Inference."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id, latitude, longitude, thumbnail_path, date_taken, location_tags FROM photos WHERE latitude IS NOT NULL')
    rows = c.fetchall()
    explicit_gps = [dict(r) for r in rows]
    
    # Get all photos without GPS but with timestamps
    c.execute('SELECT id, thumbnail_path, date_taken, location_tags FROM photos WHERE latitude IS NULL AND date_taken != ""')
    no_gps = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    if not explicit_gps:
        return []

    # Simple Temporal Inference logic
    # To keep it fast, we convert explicit GPS photos into a sorted list by time
    import dateutil.parser as dparser
    
    def parse_time(t_str):
        try:
            return dparser.parse(t_str.replace(':', '-', 2)) # EXIF uses 2023:01:01
        except:
            return None

    explicit_sorted = []
    for p in explicit_gps:
        dt = parse_time(p['date_taken'])
        if dt: explicit_sorted.append((dt.timestamp(), p))
    explicit_sorted.sort(key=lambda x: x[0])
    
    explicit_timestamps = [x[0] for x in explicit_sorted]
    window = 3600
    results = explicit_gps
    
    for p in no_gps:
        dt = parse_time(p.get('date_taken', ''))
        if not dt: continue
        ts = dt.timestamp()
        
        # Find closest match using binary search on timestamps
        import bisect
        idx = bisect.bisect_left(explicit_timestamps, ts)
        
        best_match = None
        min_diff = window + 1
        
        # Check neighbors
        for i in [idx - 1, idx]:
            if 0 <= i < len(explicit_sorted):
                cand_ts, cand_photo = explicit_sorted[i]
                diff = abs(ts - cand_ts)
                if diff < min_diff:
                    min_diff = diff
                    best_match = cand_photo

        if best_match:
            results.append({
                "id": p.get("id"),
                "thumbnail_path": p.get("thumbnail_path"),
                "latitude": best_match.get("latitude"),
                "longitude": best_match.get("longitude"),
                "location_tags": p.get("location_tags"),
                "is_inferred": True,
                "date_taken": p.get("date_taken")
            })

    import random
    for r in results:
        r["latitude"] = float(r["latitude"]) + random.uniform(-0.005, 0.005)
        r["longitude"] = float(r["longitude"]) + random.uniform(-0.005, 0.005)
            
    return results

@app.get("/api/maintenance/duplicates")
async def get_duplicates(threshold: int = 8):
    """Detect Near-Duplicates using Hamming distance on pHash."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, file_path, phash, thumbnail_path, date_taken FROM photos WHERE phash IS NOT NULL AND phash != ""')
    rows = c.fetchall()
    conn.close()
    
    photos = [dict(r) for r in rows]
    if len(photos) < 2:
        return []

    # Group by similarity
    # phash is a hex string (usually 16 chars for 64-bit)
    def hamming_distance(h1, h2):
        # Convert hex to int
        i1 = int(h1, 16)
        i2 = int(h2, 16)
        return bin(i1 ^ i2).count('1')

    duplicates = []
    processed = set()
    
    for i in range(len(photos)):
        if photos[i]['id'] in processed: continue
        
        group = [photos[i]]
        for j in range(i + 1, len(photos)):
            if photos[j]['id'] in processed: continue
            
            dist = hamming_distance(photos[i]['phash'], photos[j]['phash'])
            if dist <= threshold:
                group.append(photos[j])
                processed.add(photos[j]['id'])
        
        if len(group) > 1:
            duplicates.append(group)
            processed.add(photos[i]['id'])
            
    return duplicates

class PruneRequest(BaseModel):
    photo_ids: List[int]

@app.post("/api/duplicates/prune")
async def prune_duplicates(request: PruneRequest):
    """Deletes flagged duplicate photos from database and disk."""
    conn = get_connection()
    c = conn.cursor()
    
    deleted_count = 0
    errors = []
    
    for pid in request.photo_ids:
        c.execute("SELECT file_path, thumbnail_path FROM photos WHERE id = ?", (pid,))
        row = c.fetchone()
        if not row:
            continue
            
        file_path = row['file_path']
        thumb_path = row['thumbnail_path']
        
        # 1. Delete from faces table
        c.execute("DELETE FROM faces WHERE photo_id = ?", (pid,))
        # 2. Delete from photos table
        c.execute("DELETE FROM photos WHERE id = ?", (pid,))
        
        # 3. Delete from disk
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            deleted_count += 1
        except Exception as e:
            errors.append(f"Failed to delete {file_path}: {e}")
            
    conn.commit()
    conn.close()
    
    return {"status": "success", "deleted_count": deleted_count, "errors": errors}


@app.get("/api/search")
async def search_photos(query: str = "", date_start: str = "", date_end: str = "", camera: str = "", page: int = 1, limit: int = 100):
    conn = get_connection()
    c = conn.cursor()
    
    offset = (page - 1) * limit
    terms = [t.strip().lower() for t in query.replace(',', ' ').split() if t.strip()]
    
    clauses = ["1=1"]
    params = []
    
    # Search keywords
    if terms:
        for term in terms:
            t = f"%{term}%"
            clauses.append("(LOWER(pe.name) LIKE ? OR LOWER(p.location_tags) LIKE ? OR LOWER(p.file_path) LIKE ? OR LOWER(p.ai_tags) LIKE ?)")
            params.extend([t, t, t, t])
            
    # Filters
    if date_start:
        clauses.append("p.date_taken >= ?")
        params.append(date_start)
    if date_end:
        clauses.append("p.date_taken <= ?")
        params.append(date_end)
    if camera:
        clauses.append("p.camera_model LIKE ?")
        params.append(f"%{camera}%")
        
    where_clause = " AND ".join(clauses)

    # Step 1: Get total count
    c.execute(f'''
        SELECT COUNT(DISTINCT p.id) as total
        FROM photos p
        LEFT JOIN faces f ON p.id = f.photo_id
        LEFT JOIN people pe ON f.person_id = pe.id
        WHERE {where_clause}
    ''', params)
    total_count = c.fetchone()['total']

    # Step 2: Get paginated results
    c.execute(f'''
        SELECT DISTINCT p.id, p.file_path, p.location_tags, p.ai_tags, p.date_taken, p.camera_model, p.thumbnail_path, p.latitude, p.longitude
        FROM photos p
        LEFT JOIN faces f ON p.id = f.photo_id
        LEFT JOIN people pe ON f.person_id = pe.id
        WHERE {where_clause}
        ORDER BY p.date_taken DESC, p.id DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset])
    
    rows = c.fetchall()
    conn.close()
    
    return {
        "results": [dict(r) for r in rows],
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": (total_count + limit - 1) // limit
    }

@app.get("/photo/{photo_id}")
async def get_full_photo(photo_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT file_path FROM photos WHERE id = ?', (photo_id,))
    row = c.fetchone()
    conn.close()
    if row and os.path.exists(row['file_path']):
        return FileResponse(row['file_path'])
    return {"error": "Photo not found"}
