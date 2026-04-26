# Photo Manager V3.4: Intelligence Manifest
A high-performance, local-first AI photo management system with Deep Retrieval, Geocoded Atlas, Vision LLM Inference, and Precision Visual Anchoring.

## 🧬 Tactical V3.4 Stack
- **AI Core**: RetinaFace (Detection) + FaceNet512 (Recognition) + MobileNetV3 (Scene)
- **Visual Geocoder**: OpenAI CLIP (Precision Landmark Anchoring)
- **Vision LLM Geocoder**: Local Llama-3.2-Vision / Qwen2.5-VL via Ollama
- **Intelligence Layer**: V3.4 ULTIMA Hydrator (Temporal GPS, Landmark Distillation, Deductive Geo-Inference)
- **Backend**: FastAPI (Python 3.11) + SQLite3 (WAL Mode)
- **Discovery UI**: Stealth Pro V3.4 (Leaflet Atlas + Infinite Scroll + Duplicate Pruning)

## ⚡ V3.4 Breakthrough Features
- **Vision LLM Deductive Geocoding (NEW)**: Memory-safe local LLM inference (downsampled to 1280px) to deduce locations from signs, language, and architecture for photos lacking GPS.
- **Duplicate Detection & Pruning (NEW)**: Perceptual hashing (`phash`) groups near-duplicates, allowing you to bulk-prune redundant files directly from the UI.
- **Local Geo-Heatmap (NEW)**: Offline density heatmap visualization of your entire photo library, seamlessly togglable on the Geocoded Atlas.
- **Visual Landmark Precision**: CLIP-based recognition identifies specific landmarks (e.g., Colosseum, Taj Mahal) to upgrade generic country GPS into high-precision map coordinates.
- **Geocoded Atlas**: Leaflet marker clustering handles large-scale libraries, shattering density bubbles into individual inspectable assets.
- **Temporal Propagation**: Automatically propagates GPS data to non-GPS photos in the same session.

## 🚀 Quick Start
1.  **Clone & Install**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Launch**:
    Run `run.bat` (Self-healing protocol clears port 8000 and restarts server).
3.  **Hydrate Precision**:
    Run `python tools/hydrate_metadata.py` to upgrade your library with visual landmarks.
4.  **UI**:
    Access the tactical dashboard at `http://localhost:8000`.

## 🛠️ Operational Support
All major V1-V2 bugs have been resolved. See [docs/bug_fixes.md](file:///c:/Raghava/Antigravity/photo_manager/docs/bug_fixes.md) for the full resolution log.

---

## 🏗️ Architecture & Decision Rationale

The Photo AI Manager is designed for **total privacy** and **high-performance local compute**. Every architectural choice prioritizes these two goals over cloud scalability.

### Architecture Overview
The system follows a **Monolithic API + Threaded Worker** pattern.

```mermaid
graph TD
    UI[Glassmorphism UI] <-->|HTTP| API(FastAPI Server)
    API -.->|Spawn Thread| Scanner[[Background Scanner]]
    Scanner -->|Read| Disk[External Drives]
    Scanner -->|Compute| AI[DeepFace/PyTorch AI Engine]
    Scanner -->|Write| DB[(SQLite Database)]
    API <-->|Search| DB
    API -->|Serve| Thumb[Thumbnail Cache]
    Hydrate[[Hydration Engine]] -->|CLIP / Geo| DB
```

### Why These Decisions?
-   **FastAPI**: Chosen for its native asynchronous support, which allows the UI to poll the scanner's progress without blocking the main event loop.
-   **SQLite (`index.db`)**: Provides a zero-config, portable database that lives alongside your photos. It lacks the overhead of Postgres but handles 10,000+ photos with sub-millisecond query times.
-   **Facenet512 (AI Engine)**: We chose `Facenet512` over standard `dlib` or `MTCNN` because it provides 4x more biometric detail per face, significantly reducing "masking" errors.
-   **CLIP Geocoder**: Deployed in V3.3 to bridge the gap between "Country Name" folder tags and physical map coordinates using zero-shot image-to-text matching.
-   **Vanilla JS/CSS**: By avoiding React or Tailwind, we keep the frontend lightweight and ensure the project remains functional for years without dependency rot.

```mermaid
graph TD
    %% Define Nodes
    UI[Web Interface HTML/JS]
    API(FastAPI Backend)
    Scanner[[Background Scanner]]
    FaceUtil(DeepFace / PyTorch GPU Engine)
    DB[(SQLite Database)]
    Disk[External Photo Drives]
    Thumb[Thumbnail Cache]
    Tools[CLI Diagnostic Tools]

    %% Interactions
    UI <-->|HTTP Requests| API
    
    %% Scanner interactions
    API -.->|Triggers| Scanner
    Scanner -->|Reads original photos| Disk
    Scanner -->|1. Sends image array| FaceUtil
    FaceUtil -->|2. Returns 512-d encoding & Box| Scanner
    FaceUtil -->|Transforms| Thumb
    Scanner -->|3. Writes encodings & Paths| DB
    
    %% Read operations
    API <-->|SQL Queries| DB
    API -->|Serves| Thumb
    API -->|Serves Full Photo| Disk
    
    %% Maintenance
    Tools <-->|Database Checks| DB
    
    %% Styling
    classDef web fill:#10b981,stroke:#047857,stroke-width:2px,color:white;
    classDef python fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:white;
    classDef database fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:white;
    
    class UI web;
    class API python;
    class Scanner python;
    class FaceUtil python;
    class DB database;
```

---

## 🚀 Key Features

*   **512-d Recognition**: Upgraded from 128-d to **Facenet512**, providing 4x higher detail per face for commercial-grade accuracy.
*   **Auto-Recognition**: AI "remembers" people you have already named and automatically tags them in new scans.
*   **AI Scene Intelligence**: Integrated **MobileNetV3** for 1,000-category object recognition (German Shepherd, Lion, Sunset, etc.) with a 0.5 confidence floor.
*   **Multi-Term Search**: Supports powerful keyword combinations like "Kenya Lion" using refined AND-logic.
*   **Search Pagination**: Highly scalable search interface that can handle thousands of results with snappy Next/Prev controls.
*   **Detection Reliability**: Automatic in-memory image downsampling (to 1280px) ensures face detection never fails on high-resolution (10MB+) photos.

---

## 📂 Script Breakdown

### 1. `main_backend.py` (The V2 Hub)
Runs the `FastAPI` server. It supports:
- **High-Density Telemetry**: CPU, RAM, and AI Health stats via `psutil`.
- **Advanced Search**: Multi-dimensional filtering by **Date Range**, **Camera Model**, and **GPS Location**.
- **Duplicate Management**: Identifies and clusters near-duplicate files using `phash`, exposing endpoints for disk-level pruning.

### 2. `scanner.py` (The Precision Engine)
Upgraded indexing lifter:
- **EXIF Extraction**: Now extracts GPS (Lat/Long), Device Make/Model, and technical ISO/Aperture settings.
- **Fingerprinting**: Generates and stores 512-d biometric vectors.
- **Scene Awareness**: Runs the 1,000-class object classifier to tag 'Lions', 'Dogs', and 'Places'.

### 3. `tools/hydrate_metadata.py` & `tools/vision_llm_geocoder.py`
The intelligence engines run separately to ensure the API never blocks.
- **Phase 6 (CLIP)**: Matches visual landmarks.
- **Phase 7 (Ollama)**: Uses local Vision LLMs to contextually deduce locations from text and architecture.

### 3. `templates/` & `static/`
A complete UI redesign following the **Stealth Pro** design system:
- **Aesthetic**: Abyss Black (#000000) with Racing Red and Electric Yellow accents.
- **Navigation**: Horizontal **Tabbed Architecture** for a professional workflow.
- **Visualization**: **Chart.js** integration for real-time telemetry gauges.

---

## ⚙️ Running the Project / GitHub Setup Guide

If you are cloning this from GitHub, follow these instructions to stand up your own local, privacy-first photo manager:

### Prerequisites
1. **Python 3.10+**: Ensure Python is installed.
2. **Ollama**: (Optional but Recommended) Install [Ollama](https://ollama.com/) locally to enable the Vision Geocoder. Pull a vision model: `ollama run llama3.2-vision`.

### Installation
1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/photo_manager.git
    cd photo_manager
    ```
2. **Create a Virtual Environment** (Highly Recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```
3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Execution
1. **Start the Core API**:
   Always use **`run.bat`** on Windows. This ensures `PYTHONUTF8=1` is set, preventing console crashes caused by emojis in AI libraries. On Mac/Linux, run:
   ```bash
   PYTHONUTF8=1 uvicorn main_backend:app --host 0.0.0.0 --port 8000
   ```
2. **Access the Dashboard**:
   Open `http://localhost:8000` in your browser.
3. **Scan Your Photos**:
   In the Scanner tab, input the absolute path to your photo directory (e.g., `D:\Photos\2023`) and click "Initialize Scan".
4. **Hydrate Intelligence (Post-Scan)**:
   Once the basic scan is done, run the intelligence pipeline in a separate terminal:
   ```bash
   python tools/hydrate_metadata.py
   ```
   This will run the CLIP landmark anchoring and the Ollama Vision LLM geocoding pipeline.
