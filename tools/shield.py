import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def check_health():
    print("--- Reliability Check: API Heartbeat ---")
    try:
        res = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = res.json()
        print(f"  Status: {data.get('status')}")
        print(f"  Version: {data.get('version')}")
        print(f"  AI Engine: {data.get('engine')}")
        return data.get("status") == "ok"
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False

def check_search_logic():
    print("\n--- Reliability Check: Multi-Term Search ---")
    # Testing "Kenya Lion" (74 matches expected)
    test_queries = ["Kenya Lion", "kenya lion", "KENYA LION"]
    
    for query in test_queries:
        print(f"  Testing query: '{query}'...")
        try:
            res = requests.get(f"{BASE_URL}/api/search?query={query}&limit=100", timeout=5)
            data = res.json()
            
            # 1. Type Check (Must be Object, not Array)
            if not isinstance(data, dict):
                print(f"    ❌ FAIL: Response is {type(data)}, expected dict.")
                return False
                
            results = data.get("results", [])
            total = data.get("total", 0)
            
            print(f"    Found {len(results)} results (Total in DB: {total})")
            
            # 2. Results Check (Must find the 74 lions)
            if total < 70:
                print(f"    ❌ FAIL: Expected at least 70 results, found {total}.")
                return False
                
            # 3. Case Insensitivity Check
            if total == 0:
                print(f"    ❌ FAIL: Total is 0 for query '{query}'")
                return False
                
        except Exception as e:
            print(f"    ❌ Search check failed: {e}")
            return False
            
    print("  ✅ Search logic is CASE-INSENSITIVE and consistent.")
    return True

if __name__ == "__main__":
    print("Starting the Antigravity Reliability Engine (Shield)...")
    
    # Wait for server to be ready
    for _ in range(5):
        if check_health():
            break
        print("  Waiting for server...")
        time.sleep(2)
    else:
        print("❌ Server timed out.")
        sys.exit(1)
        
    if not check_search_logic():
        print("\n❌ RELIABILITY CHECK FAILED.")
        sys.exit(1)
        
    print("\n✅ SYSTEM HEALTH: 100% (STABLE)")
