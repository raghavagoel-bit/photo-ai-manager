@echo off
set "PYTHONUTF8=1"
echo Starting Photo Recognition AI Server...
echo The web interface will open shortly.
start http://127.0.0.1:8000
uvicorn main_backend:app --host 127.0.0.1 --port 8000
pause
