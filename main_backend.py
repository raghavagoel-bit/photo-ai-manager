from fastapi import FastAPI, BackgroundTasks, Request, Depends, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from database import (get_all_faces, update_face_person, 
                     create_person, get_person_by_name, get_connection)
from scanner import scan_directory
from face_utils import check_models_health

app = FastAPI()

# Mount static folders
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/thumbnails", StaticFiles(directory="data/thumbnails"), name="thumbnails")

templates = Jinja2Templates(directory="templates")

# Global variables for background task state
scan_status = {"is_scanning": False, "scanned_count": 0, "face_count": 0}

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

def run_scan_task(path: str):
    global scan_status
    scan_status["is_scanning"] = True
    scan_status["scanned_count"] = 0
    scan_status["face_count"] = 0
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

@app.get("/api/health")
async def get_health():
    return check_models_health()

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
        # AgglomerativeClustering with complete linkage:
        # Only merges clusters when the FARTHEST pair of points across both clusters
        # is within the threshold. This is the most conservative strategy — it prevents
        # different people bleeding into the same cluster via a single bridge embedding.
        # Facenet512 distances: same-person pairs < 0.9, different people median=1.3.
        # Setting threshold=1.0 for a balanced conservative grouping in 512-d space.
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

@app.get("/api/search")
async def search_photos(query: str = ""):
    conn = get_connection()
    c = conn.cursor()
    # Basic search by person name or location tag
    c.execute('''
        SELECT DISTINCT p.id, p.file_path, p.location_tags, p.date_taken
        FROM photos p
        LEFT JOIN faces f ON p.id = f.photo_id
        LEFT JOIN people pe ON f.person_id = pe.id
        WHERE pe.name LIKE ? OR p.location_tags LIKE ? OR p.file_path LIKE ?
        LIMIT 100
    ''', (f"%{query}%", f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

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
