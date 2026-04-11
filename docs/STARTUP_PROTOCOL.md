# Startup Protocol (Antigravity Gold Standard)

To ensure workspace reliability and avoid regression bugs, this protocol must be executed **every time** development work begins on the Photo Manager project.

## 🏁 Mandatory Initialization

Follow these steps in order to guarantee a healthy development environment:

### 1. The One-Touch Initialization
Run the master initialization script. This clears port conflicts, verifies dependencies, and checks for AI model integrity.

```bash
python tools/initialize.py
```

### 2. Signal Verification (Heartbeat)
Launch the server (if not already handled by initialization) and run the Tactical Shield.

```bash
run.bat
python tools/shield.py
```

### 3. Deep Intelligence Sync (Post-Scan)
If you have just scanned a large new collection (like "Turkey"), run the V3 Hydrator to backfill geocoding and propagate Atlas coordinates.

```bash
python tools/hydrate_metadata.py
```

### 4. Visual UI Handshake
Open the browser at `http://localhost:8000` and perform a **Hard Refresh (Ctrl + F5)**.
*   Confirm initial tab is "Scanner."
*   Verify AI Engine is "Online."

---

## 🛠️ Troubleshoot Guide

| Symptom | Action |
| :--- | :--- |
| **Port 8000 Blocked** | `run.bat` now has auto-healing. If it fails, run `taskkill /F /IM uvicorn.exe`. |
| **Models Missing** | Check `tools/initialize.py` log. If missing, redownload RetinaFace/Facenet512. |
| **Atlas 500 Error** | Run `python tools/shield.py` to check for temporal inference edge cases. |
| **UI Overlaps** | Perform a Hard Refresh to clear CSS cache. |

---

## 📑 Governance
*   All new features **MUST** include a corresponding test case in `tools/shield.py`.
*   The `shield.py` code MUST return **100% STABLE** status before any PR is opened.
