import unittest
import requests
import time
import subprocess
import sys
import os

BASE_URL = "http://localhost:8000"

class TestAPICleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure server is running or start it? 
        # For now, we assume the user or a separate process starts it, 
        # OR we can try to start it here. 
        # Given the environment, it's safer to assume it might need starting or is running.
        # Let's check if it's running first.
        try:
            requests.get(BASE_URL, timeout=1)
        except requests.exceptions.ConnectionError:
            print("Server not running, starting it...")
            # Start server in background
            cls.server_process = subprocess.Popen(
                [sys.executable, "src/main.py", "--headless", "--port", "8000"],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5) # Wait for startup

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'server_process'):
            cls.server_process.terminate()
            cls.server_process.wait()

    def test_health_check(self):
        """Test GET / returns 200"""
        resp = requests.get(f"{BASE_URL}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["status"], ["waiting_for_game", "running"])

    def test_start_game(self):
        """Test POST /start-game returns 200"""
        resp = requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("dungeon_level", data)

    def test_game_state(self):
        """Test GET /game-state returns 200"""
        # Ensure game is started
        requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
        resp = requests.get(f"{BASE_URL}/game-state")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("player_health", data)

    def test_perform_action(self):
        """Test POST /perform-action returns 200"""
        requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
        resp = requests.post(f"{BASE_URL}/perform-action", json={"action": "w"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["action_executed"], "w")

    def test_game_screenshot_bytes(self):
        """Test GET /game-screenshot returns image/png bytes"""
        requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
        resp = requests.get(f"{BASE_URL}/game-screenshot")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "image/png")
        # Check magic bytes for PNG
        self.assertTrue(resp.content.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_removed_endpoints(self):
        """Test that removed endpoints return 404"""
        endpoints = [
            "/game-info",
            "/observation",
            "/sprite/player.png",
            "/action"
        ]
        for ep in endpoints:
            resp = requests.get(f"{BASE_URL}{ep}")
            self.assertEqual(resp.status_code, 404, f"Endpoint {ep} should be 404")

if __name__ == "__main__":
    unittest.main()
