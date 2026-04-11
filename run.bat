@echo off
set "PYTHONUTF8=1"
cd /d "%~dp0"

echo [SYSTEM] SCANNING PORT 8000...
netstat -ano | findstr /R /C:":8000.*LISTENING" > nul
if %errorlevel% equ 0 (
    echo [ALERT] PORT 8000 BLOCKED BY ACTIVE LISTENER. 
    echo [SYSTEM] ENGAGING SELF-HEALING PROTOCOL...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8000.*LISTENING"') do (
        if "%%a" NEQ "0" (
            echo [SYSTEM] TERMINATING PID %%a...
            taskkill /F /PID %%a > nul 2>&1
        )
    )
    timeout /t 2 /nobreak > nul
)

echo [SYSTEM] INITIALIZING ANTIGRAVITY PHOTOS V3...
echo [SYSTEM] SERVER STARTING ON HOST 0.0.0.0:8000
start "" http://localhost:8000
uvicorn main_backend:app --host 0.0.0.0 --port 8000 --log-level info
pause
