import requests
import time
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

BASE_URL = "http://127.0.0.1:8000"
SHIELD_VERSION = "2.0.1-Tactical"

def check_health():
    print(f"--- Tactical Shield V{SHIELD_VERSION}: API Heartbeat ---")
    try:
        res = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = res.json()
        print(f"  Status: {data.get('status')}")
        print(f"  Version: {data.get('version')}")
        return data.get("status") == "ok"
    except Exception as e:
        print(f"  [X] Health check failed: {e}")
        return False

def check_search_logic():
    print("\n--- Tactical Shield: Multi-Term Search ---")
    query = "Kenya Lion"
    try:
        res = requests.get(f"{BASE_URL}/api/search?query={query}", timeout=5)
        data = res.json()
        results = data.get("results", [])
        print(f"  Testing query: '{query}' -> Found {len(results)} results.")
        if len(results) == 0:
            print("  [FAIL] Search returned 0 results for known keywords.")
            return False
        return True
    except Exception as e:
        print(f"  [X] Search check failed: {e}")
        return False

def check_atlas_intelligence():
    print("\n--- Tactical Shield: Atlas Temporal Inference ---")
    try:
        res = requests.get(f"{BASE_URL}/api/atlas", timeout=5)
        data = res.json()
        print(f"  Atlas Payload: {len(data)} vectors detected.")
        if not isinstance(data, list):
            print("  [FAIL] Atlas API did not return a list.")
            return False
            
        inferred = [p for p in data if p.get('is_inferred')]
        print(f"  Temporal Inference: {len(inferred)} photos with propagated GPS.")
        
        # Verify lat/lng existence
        if len(data) > 0:
            sample = data[0]
            if 'latitude' not in sample or 'longitude' not in sample:
                print("  [FAIL] Atlas vectors missing coordinates.")
                return False
        return True
    except Exception as e:
        print(f"  [X] Atlas intelligence check failed: {e}")
        return False

def check_maintenance_logic():
    print("\n--- Tactical Shield: Duplicate Detection ---")
    try:
        res = requests.get(f"{BASE_URL}/api/maintenance/duplicates", timeout=5)
        data = res.json()
        print(f"  Maintenance Hub: {len(data)} duplicate groups identified.")
        if not isinstance(data, list):
            print("  [FAIL] Maintenance API did not return a list.")
            return False
        return True
    except Exception as e:
        print(f"  [X] Maintenance check failed: {e}")
        return False

def check_telemetry():
    print("\n--- Tactical Shield: AI Health Telemetry ---")
    try:
        res = requests.get(f"{BASE_URL}/api/telemetry", timeout=10)
        data = res.json()
        print(f"  AI Score: {data.get('ai_score')}")
        print(f"  Total Photos in DB: {data.get('total_photos')}")
        if data.get('ai_score', 0) < 0.9:
            print("  [WARN] AI Engine confidence is below threshold!")
        return True
    except Exception as e:
        print(f"  [X] Telemetry check failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting the Antigravity Tactical Shield V{SHIELD_VERSION}...")
    
    # Wait for server to be ready
    server_ready = False
    for i in range(5):
        if check_health():
            server_ready = True
            break
        print(f"  [{i+1}/5] Waiting for server at {BASE_URL}...")
        time.sleep(2)
        
    if not server_ready:
        print("\n[CRITICAL] Server is offline. Automated QA aborted.")
        sys.exit(1)
        
    # Run Tiered Tests
    results = [
        check_search_logic(),
        check_atlas_intelligence(),
        check_maintenance_logic(),
        check_telemetry()
    ]
    
    if all(results):
        print("\n" + "="*40)
        print("  SYSTEM STABILITY: 100% (STABLE)")
        print("="*40)
        sys.exit(0)
    else:
        print("\n" + "!"*40)
        print("  SYSTEM STABILITY: REGRESSION DETECTED")
        print("!"*40)
        sys.exit(1)
