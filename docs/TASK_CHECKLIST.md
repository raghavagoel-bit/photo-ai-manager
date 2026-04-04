# Photo AI Manager — Compiled Task Checklist

Complete record of all tasks completed across all sessions.

---

## Phase 1: Initial Architecture & V1 UI

- [x] Set up `FastAPI` backend with `uvicorn` dev server.
- [x] Designed `SQLite` schema — `photos`, `faces`, `people` tables.
- [x] Built `database.py` with full CRUD helpers.
- [x] Built `scanner.py` — recursive directory walker with smart hash-based skip.
- [x] Integrated `exifread` for `DateTimeOriginal` and GPS location tagging.
- [x] Served `templates/index.html` — glassmorphism UI with 3 views (Scanner, Tag Faces, Search).
- [x] Mounted `/static` and `/thumbnails` static file routes.
- [x] Created `.gitignore` excluding `data/` for privacy.
- [x] Built `run.bat` for one-click server launch.

---

## Phase 1.5: Bug Fixes & Debugging

- [x] **0 Photos Processed Bug** — Fixed mutating `status_dict` in background scanner thread.
- [x] **422 Unprocessable Entity Bug** — Fixed FastAPI `BackgroundTasks` + `Form(...)` dependency order.
- [x] **Dlib segfault on Windows** — Identified missing cuDNN bindings as root cause; decided to migrate engine.

---

## Phase 2: AI Engine — dlib → DeepFace/PyTorch

- [x] Removed `dlib`, `face_recognition` from `requirements.txt`.
- [x] Added `deepface`, `torch`, `torchvision` to `requirements.txt`.
- [x] Rewrote `face_utils.py` using `DeepFace.represent()`.
- [x] Set detector to `RetinaFace` (GPU-accelerated PyTorch).
- [x] Set encoder to `Facenet` (128-d embeddings).
- [x] Added bounding box cropping and 150×150 thumbnail saving per face.
- [x] Guarded against negative/invalid bounding box coordinates from DeepFace.

---

## Phase 3: Scanning Robustness

- [x] Added `is_scanned()` check to skip already-indexed files on repeat scans.
- [x] Implemented live status polling via `/api/scan/status` endpoint.
- [x] Added per-file progress logging: `Scanning [N]: file.jpg (XMB)...`
- [x] Built `/api/search` endpoint — searches by person name, location, or file path.
- [x] Built `/photo/{photo_id}` endpoint for full-resolution photo serving.

---

## Phase 4: AI Face Clustering / Deduplication

- [x] Installed `scikit-learn` dependency.
- [x] Implemented DBSCAN clustering in `/api/faces?cluster=true` endpoint.
- [x] Each cluster returns: `{ id, thumbnail, clone_ids[] }`.
- [x] Frontend reads `clone_ids.length` and shows "Who is this? (N clones)" per card.
- [x] Built `/api/faces/bulk_tag` endpoint — tags all clone IDs in one API call.
- [x] Updated `script.js` to submit `clone_ids` array on name entry.

---

## Bug Fix Session 1: Clustering Epsilon Miscalibration

- [x] Diagnosed over-clustering: `eps=10.0` is far too large for normalized Facenet space.
- [x] Wrote `analyze_distances.py` to compute pairwise Euclidean distances and sweep `eps` values.
- [x] Data-driven result: optimal `eps=0.5` for old non-normalized embeddings (18 clusters).
- [x] Applied L2 normalization to all embeddings in `face_utils.py` before storage.
- [x] Updated `main_backend.py` to use `eps=0.5`.

---

## Bug Fix Session 2: Zero Faces — Corrupt Model Weights

- [x] Diagnosed silent failure: `facenet_weights.h5` was corrupt (interrupted download).
- [x] Identified root cause: DeepFace raises `ValueError` for weight load failure, **same as** "no face found" — both were silently caught.
- [x] Deleted corrupt `facenet_weights.h5` from `C:\Users\admin\.deepface\weights\`.
- [x] Manually re-downloaded `facenet_weights.h5` (88 MB) via `Invoke-WebRequest`.
- [x] `retinaface.h5` (119 MB) auto-downloaded on next run.
- [x] Made `ValueError` handler verbose — prints exact DeepFace message.
- [x] Added `traceback.print_exc()` to all generic `Exception` catches in `face_utils.py`.
- [x] Verified: `SUCCESS: 1 face(s)!` on real test image.

---

## Bug Fix Session 3: Clustering Too Loose After Re-scan

- [x] Ran `analyze_distances.py` on fresh DB (807 L2-normalized faces).
- [x] Confirmed all embedding norms = 1.0000 (perfect normalization).
- [x] Identified new distance distribution: min=0.11, 5th‰=0.80, median=1.29, max=1.64.
- [x] Ran full `eps` sweep from 0.3 to 1.1 in 0.05 increments.
- [x] Data-driven result: `eps=0.80` gives 58 clusters (natural gap at 5th percentile).
- [x] Updated `main_backend.py` to use `eps=0.8`.
- [x] Restarted server — clustering now tighter.

---

## Phase 4b: Upgrade to AgglomerativeClustering

- [x] Ran `compare_clustering.py` — swept DBSCAN vs `single`/`average`/`complete` linkage across 13 threshold values.
- [x] Identified `complete` linkage eliminates chaining problem that caused different people to merge.
- [x] Data-driven result: `complete` at `threshold=0.85` gives 68 clusters (vs 56 with DBSCAN) — purer groupings.
- [x] Replaced `DBSCAN` import with `AgglomerativeClustering` in `main_backend.py`.
- [x] Parameters set: `n_clusters=None`, `distance_threshold=0.85`, `metric='euclidean'`, `linkage='complete'`.
- [x] Verified labels API is identical — no frontend changes needed.
- [x] Restarted server — Tag Faces now shows ~68 purer clusters.

---

## Documentation

## Phase 5: Reliability & Testing

- [x] Implemented `check_models_health()` in `face_utils.py` with byte-size verification.
- [x] Added startup health check to `main_backend.py` (with Windows encoding fix for emojis).
- [x] Integrated health check into `/api/scan` to block scanning if models are corrupt.
- [x] Implemented cluster 'diameter' based confidence scoring in the backend.
- [x] Added real-time AI Engine status indicator to the sidebar.
- [x] Added color-coded confidence badges (🟢/🟡/🔴) to face cards in the UI.
- [x] Verified all systems via HTTP and manual server boot tests.

---

## Documentation

- [x] Created `photo_manager/docs/` directory.
- [x] Saved consolidated `IMPLEMENTATION_PLAN.md` with all phases and bugs.
- [x] Saved this compiled `TASK_CHECKLIST.md`.
- [x] Updated both docs with Phase 4b (AgglomerativeClustering).
- [x] Updated master plan with Phase 5 detailed testing protocols.
---

## Phase 6: AI Ultra-Accuracy Upgrade (✅ Completed)

- [x] Swapped 128-d `Facenet` for **512-d `Facenet512`** in `face_utils.py`.
- [x] Implemented `reset_faces.py` tool for high-fidelity migration.
- [x] Verified 512 float values are stored exactly in `index.db`.
- [x] **Clustering Recalibration**: Updated `AgglomerativeClustering` threshold from `0.85` to `1.0`.
- [x] Updated health checks for the new `facenet512_weights.h5` file.

---

## Bug Fix Session 4: Windows Unicode & Weight Recovery (✅ Fixed)

- [x] **Windows encoding bug**: Fixed `UnicodeEncodeError` in console logs by setting `PYTHONUTF8=1` in `run.bat`.
- [x] **Manual Weights Recovery**: Manually recovered `facenet512_weights.h5` after auto-download failed.
- [x] **Health Check refinement**: Refined code to allow server boot even if models are missing (permitting auto-download on first scan) while still identifying corrupt files.
- [x] **Organize Tools**: Moved `debug_face_512.py`, `analyze_distances.py`, `check_db.py`, and `reset_faces.py` to `tools/` folder.

---

## Phase 6.b: Detection Reliability (✅ Completed)

### Goal
Fix "Zero Faces Detected" bug on high-resolution (8MB+) images.

### 6.b.1: In-Memory Downsampling
- Updated `process_image` in `face_utils.py` to use `cv2` for image loading.
- Added logic to scale images down to a maximum dimension of `1280px` before feeding to `RetinaFace`.
- **Reason**: Face recognition models are trained on low-res images and struggle with 4000px+ images on standard CPUs.

### 6.b.2: Box Coordinate Rescaling
- Mapped the bounding box coordinates returned from the scaled image back to the original image dimensions.
- Allows `PIL` to crop out the high-resolution face for the thumbnail.

---

## Phase 7: V2 UI Redesign (⏳ Pending — awaiting Stitch MCP)
 configuration. Once enabled, scaffold `v2_ui/` at `/v2` route based on Stitch design tokens.
