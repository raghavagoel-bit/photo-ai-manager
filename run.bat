@echo off
set "PYTHONUTF8=1"
echo [SYSTEM] INITIALIZING ANTIGRAVITY PHOTOS V2...
echo [SYSTEM] SERVER STARTING ON PORT 8000
timeout /t 3 /nobreak > nul
start http://localhost:8000
uvicorn main_backend:app --host 0.0.0.0 --port 8000
pause
