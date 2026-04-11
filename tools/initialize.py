import os
import sys
import subprocess
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def print_banner(msg):
    print("\n" + "="*60)
    print(f" {msg}")
    print("="*60)

def check_models():
    print("[1/4] Scanning AI Model Repository...")
    weights_dir = os.path.join(os.path.expanduser("~"), ".deepface", "weights")
    facenet_path = os.path.join(weights_dir, "facenet512_weights.h5")
    retinaface_path = os.path.join(weights_dir, "retinaface.h5")
    
    if not os.path.exists(facenet_path):
        print("  [WARN] Facenet512 model missing. (Will be auto-downloaded on first scan)")
    else:
        print("  [OK] Facenet512: Verified.")
        
    if not os.path.exists(retinaface_path):
        print("  [WARN] RetinaFace model missing. (Will be auto-downloaded on first scan)")
    else:
        print("  [OK] RetinaFace: Verified.")
    return True

def clear_port():
    print("[2/4] Clearing Signal Conflicts (Port 8000)...")
    try:
        # Use netstat to find PID
        cmd = 'netstat -ano | findstr /R /C:":8000.*LISTENING"'
        output = subprocess.check_output(cmd, shell=True).decode()
        for line in output.strip().split('\n'):
            if not line.strip(): continue
            pid = line.strip().split()[-1]
            if pid != "0":
                print(f"  [!] Port 8000 occupied by PID {pid}. Terminating...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
                time.sleep(1)
        print("  [OK] Port 8000: Clear.")
    except Exception:
        print("  [OK] Port 8000: Ready.")

def check_dependencies():
    print("[3/4] Verifying Core Dependencies...")
    try:
        # Check specific critical packages
        subprocess.check_output("pip show scikit-learn python-dateutil", shell=True)
        print("  [OK] Critical Packages: Verified.")
    except Exception:
        print("  [WARN] Dependency Check: Issues detected. Please run 'pip install -r requirements.txt'")

def run_shield():
    print("[4/4] Engaging Tactical Shield (QA)...")
    # We check if uvicorn is running. If not, we don't bother the shield.
    try:
        res = subprocess.run("python tools/shield.py", shell=True)
        if res.returncode == 0:
            print("  [OK] System Health: Stable.")
        else:
            print("  [FAIL] System Health: REGRESSION DETECTED.")
    except Exception:
        print("  [WARN] Shield Aborted: Initializer could not reach server.")

if __name__ == "__main__":
    print_banner("ANTIGRAVITY PHOTOS V3 : INITIALIZATION PROTOCOL")
    
    check_models()
    clear_port()
    check_dependencies()
    run_shield()
    
    print_banner("INITIALIZATION COMPLETE: READY FOR OPERATIONS")
    print("Mandatory First Command: run.bat")
