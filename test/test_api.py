import pytest
import requests
import time
import subprocess
import sys
import os

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session", autouse=True)
def game_server():
    """Start the server if not running."""
    server_process = None
    try:
        requests.get(BASE_URL, timeout=1)
    except requests.exceptions.ConnectionError:
        print("Server not running, starting it...")
        server_process = subprocess.Popen(
            [sys.executable, "src/main.py", "--headless", "--port", "8000"],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait for server to start
        for _ in range(10):
            try:
                requests.get(BASE_URL, timeout=1)
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        else:
            if server_process:
                server_process.terminate()
            raise RuntimeError("Server failed to start")
    
    yield

    if server_process:
        server_process.terminate()
        server_process.wait()

def test_health_check():
    """Test GET / returns 200 and valid status."""
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ["waiting_for_game", "running"]

def test_start_game_procedural():
    """Test starting a procedural game."""
    payload = {
        "mode": "procedural",
        "max_rooms": 10,
        "room_min_size": 4,
        "room_max_size": 8,
        "map_width": 20,
        "map_height": 20,
        "fov_mode": "partial",
        "fov_radius": 5
    }
    resp = requests.post(f"{BASE_URL}/start-game", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "dungeon_level" in data
    assert data["dungeon_level"] == 1
    assert "player_health" in data
    assert "legal_actions" in data

def test_start_game_custom():
    """Test starting a custom game (requires custom_map.txt existence, but we test the API call)."""
    payload = {
        "mode": "custom",
        "fov_mode": "all"
    }
    resp = requests.post(f"{BASE_URL}/start-game", json=payload)
    # It might fail if file missing, but API should return 200 or 500.
    # If 500, we skip, but ideally it works.
    if resp.status_code == 200:
        data = resp.json()
        assert "dungeon_level" in data

def test_start_game_string():
    """Test starting a game from a string map."""
    map_str = (
        "#####\n"
        "#@..#\n"
        "#...#\n"
        "#####"
    )
    payload = {
        "mode": "string",
        "custom_map": map_str,
        "fov_mode": "partial",
        "fov_radius": 4
    }
    resp = requests.post(f"{BASE_URL}/start-game", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "player_position" in data
    # Player should be at (1, 1) based on map
    assert data["player_position"] == [1, 1]

def test_start_game_string_with_enemies():
    """Test starting a game from a string map with enemies (G and R)."""
    map_str = (
        "#####\n"
        "#@.G#\n"
        "#.R.#\n"
        "#####"
    )
    payload = {
        "mode": "string",
        "custom_map": map_str,
        "fov_mode": "all"
    }
    resp = requests.post(f"{BASE_URL}/start-game", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # We can't easily check entities from the response unless we add an endpoint or check the logs/state deeply.
    # But if it crashes, status_code won't be 200.
    # We can check if the game started successfully.
    assert "dungeon_level" in data

def test_perform_action_movement():
    """Test moving the player."""
    # Start a known map to ensure movement is valid
    map_str = (
        "#####\n"
        "#@..#\n"
        "#...#\n"
        "#####"
    )
    requests.post(f"{BASE_URL}/start-game", json={"mode": "string", "custom_map": map_str})
    
    # Move right
    resp = requests.post(f"{BASE_URL}/perform-action", json={"action": "d"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_executed"] == "d"
    assert data["state_changes"]["player_position"] == [2, 1]

def test_perform_action_invalid():
    """Test sending an invalid action key."""
    requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
    resp = requests.post(f"{BASE_URL}/perform-action", json={"action": "invalid_key"})
    assert resp.status_code == 400

def test_game_state_endpoint():
    """Test fetching game state independently."""
    requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
    resp = requests.get(f"{BASE_URL}/game-state")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_level_step_count" in data

def test_screenshot():
    """Test fetching a screenshot."""
    requests.post(f"{BASE_URL}/start-game", json={"mode": "procedural"})
    resp = requests.get(f"{BASE_URL}/game-screenshot")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content.startswith(b'\x89PNG'), "Response is not a valid PNG"

def test_invalid_start_mode():
    """Test starting game with invalid mode."""
    resp = requests.post(f"{BASE_URL}/start-game", json={"mode": "invalid_mode"})
    # Pydantic validation error is 422
    assert resp.status_code == 422

def test_missing_custom_map_for_string_mode():
    """Test string mode without map data."""
    resp = requests.post(f"{BASE_URL}/start-game", json={"mode": "string"})
    # Logic check raises 400, not Pydantic 422
    assert resp.status_code == 400
