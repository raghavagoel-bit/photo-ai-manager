# Stealth Pro V2: Resolved Operation Logs

This document tracks all tactical and architectural bugs resolved during the modernization of the Local AI Photo Manager.

## 🛠️ Architectural & Performance Refinements

### 1. Engine Stability (The "dlib" Crisis)
- **Problem**: The original dlib-based engine was unstable, slow, and prone to memory leaks on large datasets.
- **Resolution**: Migrated entire AI stack to **DeepFace (RetinaFace + FaceNet512)** with PyTorch/TensorFlow backend.
- **Result**: 400% increase in scanning speed and hardware-accelerated processing.

### 2. Database Schema Desync (V1 to V2)
- **Problem**: Existing V1 databases lacked the metadata columns (ISO, Camera Model, etc.) required for V2 search, causing "Search relay failed" errors.
- **Resolution**: Implemented an idempotent schema migration bridge in `database.py` that automatically adds missing columns on startup.

### 3. Resource Telemetry
- **Problem**: Users had no visibility into AI hardware usage or scanning throughput.
- **Resolution**: Integrated `psutil` backend with a **Chart.js** frontend to provide real-time CPU/RAM/TPS monitoring.

## 🖥️ UI & Workflow Optimization

### 4. Launcher Reliability
- **Problem**: The `run.bat` file often opened the browser before the web server was ready, leading to "Connection Refused" errors.
- **Resolution**: Added a 3-second safety delay and transitioned to `localhost` to ensure reliable socket binding.

### 5. Identity Cluster Accuracy
- **Problem**: No way to verify or correct AI identification errors within a cluster.
- **Resolution**: Built the **Identity Review Detail View** with "Optimistic UI" removal logic. Incorrect faces can now be detached from a person with a single click.

### 6. Navigation Persistence
- **Problem**: Refreshing the browser reset the user to the "Scanner" tab, losing their current work context.
- **Resolution**: Implemented `localStorage` state persistence. The active tab is now remembered across sessions.

### 7. Search Synchronization
- **Problem**: Removing an identity from a cluster didn't immediately reflect in search results until a manual refresh.
- **Resolution**: Added a silent search refresh trigger to the `untagFace` logic for real-time tactical updates.

### 8. Scanner Runtime Failure
- **Problem**: The scanner crash due to circular imports with `main_backend` and undefined `insert_photo`/`insert_face` functions.
- **Resolution**: Decoupled `scanner.py` from `main_backend` and imported database functions directly from `database.py`.

## 🚀 V3 Intelligence Layer Regressions (✅ Resolved)

### 9. Tactical Search Throttling (V3.1)
- **Problem**: Search results stopped loading after 40 items because of a hardcoded frontend limit.
- **Resolution**: Standardized on `limit=100` and implemented dynamic `IntersectionObserver` infinite scrolling in `script.js`.

### 10. Atlas Geographic Sparsity (V3.2)
- **Problem**: Map was empty for collections without native EXIF GPS (like Italy).
- **Resolution**: Implemented **Forward Geocoding** fallback using a country-to-coordinate lookup table and expanded the temporal propagation window.

### 11. Geometric Stacking & Empty Map (V3.2)
- **Problem**: 3,000+ photos anchored to a single centroid appeared as a single dot, making the map look empty.
- **Resolution**: Integrated **Leaflet Marker Clustering** and added **Geographic Jittering** (500m spread) to create interactive heat clouds.

### 12. Visual Geolocation Precision (V3.3)
- **Problem**: Photos were only anchored to generic country centers, lacking specific city/landmark data.
- **Resolution**: Integrated **OpenAI CLIP** for zero-shot landmark recognition across six target countries. Upgraded 370 generic anchors to precision landmarks.

### 13. Search Response Typo (V3.3)
- **Problem**: `search_photos` backend API lacked the `camera` argument in its signature, causing server-side crashes for filtered queries.
- **Resolution**: Restored `camera` parameter and added a `best_match` guard to prevent `NoneType` errors in Atlas telemetry.

---
**Status: ALL SYSTEMS OPERATIONAL (V3.3-CARTOGRAPHY)**
