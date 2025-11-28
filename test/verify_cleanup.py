import requests
import time
import sys
import base64

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, expected_status, json_data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        
        if response.status_code == expected_status:
            print(f"[PASS] {method} {path} returned {response.status_code}")
            return True
        else:
            print(f"[FAIL] {method} {path} returned {response.status_code}, expected {expected_status}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {method} {path} failed: {e}")
        return False

def verify_cleanup():
    print("Verifying API Cleanup...")
    
    # 1. Test remaining endpoints (Should PASS)
    print("\n--- Testing Remaining Endpoints ---")
    if not test_endpoint("GET", "/", 200): # Health check kept
        sys.exit(1)
        
    # Start game first
    if not test_endpoint("POST", "/start-game", 200, {"mode": "procedural"}):
        sys.exit(1)
        
    test_endpoint("GET", "/game-state", 200)
    test_endpoint("GET", "/game-screenshot", 200)
    test_endpoint("POST", "/perform-action", 200, {"action": "w"})

    # 2. Test removed endpoints (Should FAIL with 404)
    print("\n--- Testing Removed Endpoints ---")
    test_endpoint("GET", "/game-info", 404)
    test_endpoint("GET", "/observation", 404)
    test_endpoint("GET", "/sprite/player.png", 404)
    test_endpoint("POST", "/action", 404, {"action": "w"})

if __name__ == "__main__":
    # Wait a bit for server to start if run immediately after
    time.sleep(2)
    verify_cleanup()
