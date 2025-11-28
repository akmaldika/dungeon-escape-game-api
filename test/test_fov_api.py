#!/usr/bin/env python3
"""
Quick test script to verify FOV API functionality.
Run this while the API server is running to test different FOV modes.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_fov_mode(mode_config, description):
    """Test a specific FOV configuration."""
    print(f"\n=== Testing: {description} ===")
    
    try:
        # Start game with specific FOV config
        response = requests.post(f"{API_BASE}/start-game", json=mode_config)
        if response.status_code == 200:
            print("✓ Game started successfully")
            state = response.json()
            print(f"  Dungeon Level: {state['dungeon_level']}")
            print(f"  Player Health: {state['player_health']}")
            
            # Get observation to check FOV
            obs_response = requests.get(f"{API_BASE}/observation")
            if obs_response.status_code == 200:
                obs = obs_response.json()
                visible_count = sum(sum(row) for row in obs['visible_mask'])
                total_tiles = len(obs['visible_mask']) * len(obs['visible_mask'][0])
                print(f"  Visible tiles: {visible_count}/{total_tiles} ({visible_count/total_tiles*100:.1f}%)")
                
                # Test a movement action
                move_response = requests.post(f"{API_BASE}/perform-action", json={"action": "w"})
                if move_response.status_code == 200:
                    print("✓ Movement action successful")
                else:
                    print(f"✗ Movement failed: {move_response.status_code}")
            else:
                print(f"✗ Observation failed: {obs_response.status_code}")
        else:
            print(f"✗ Game start failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")

def main():
    print("FOV API Test Script")
    print("Make sure the API server is running on localhost:8000")
    
    # Test configurations
    test_configs = [
        {
            "config": {"mode": "procedural"},
            "desc": "Default FOV (partial, radius 8)"
        },
        {
            "config": {"mode": "procedural", "fov_mode": "all"},
            "desc": "All visible (no fog of war)"
        },
        {
            "config": {"mode": "procedural", "fov_mode": "partial", "fov_radius": 12},
            "desc": "Partial FOV with radius 12"
        },
        {
            "config": {"mode": "procedural", "fov_mode": "partial", "fov_radius": 4},
            "desc": "Partial FOV with radius 4"
        },
        {
            "config": {
                "mode": "procedural", 
                "max_rooms": 20, 
                "map_width": 25, 
                "map_height": 25,
                "fov_mode": "all"
            },
            "desc": "Small map with all visible"
        }
    ]
    
    for test_config in test_configs:
        test_fov_mode(test_config["config"], test_config["desc"])
        time.sleep(1)  # Brief pause between tests
    
    print("\n=== Test Summary ===")
    print("If all tests passed, FOV configuration is working correctly!")
    print("\nUsage examples:")
    print("curl -X POST 'http://localhost:8000/start-game' -H 'Content-Type: application/json' -d '{\"mode\": \"procedural\", \"fov_mode\": \"all\"}'")
    print("curl -X POST 'http://localhost:8000/start-game' -H 'Content-Type: application/json' -d '{\"mode\": \"procedural\", \"fov_radius\": 12}'")

if __name__ == "__main__":
    main()