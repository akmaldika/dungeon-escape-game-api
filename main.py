#!/usr/bin/env python3
"""
Enhanced main.py with pygame rendering and dual control (keyboard + API)
Uses pygame for pixel-perfect rendering and screenshots while keeping tcod for FOV/pathfinding.
"""

import traceback
import threading
import time
from typing import Optional, Dict, List
import queue
import io

# FastAPI imports
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import uvicorn

# Game imports
import tcod
import color
import exceptions
import setup_game
import input_handlers
from dotenv import load_dotenv
from custom_map_loader import load_custom_map_from_string

# New pygame renderer
from pygame_renderer import PygameRenderer, PygameEventConverter
import pygame

# Global game state for thread-safe communication
class ThreadSafeGameState:
    def __init__(self):
        self.lock = threading.Lock()
        self.engine = None  # Type: Engine
        self.handler: Optional[input_handlers.BaseEventHandler] = None
        self.renderer: Optional[PygameRenderer] = None
        self.current_level_step_count = 0
        self.is_running = True
        self.action_queue = queue.Queue()  # For API actions
        
    def set_game_components(self, engine, handler, renderer):
        with self.lock:
            self.engine = engine
            self.handler = handler
            self.renderer = renderer
    
    def update_handler(self, new_handler):
        with self.lock:
            self.handler = new_handler
    
    def get_state_snapshot(self):
        """Get thread-safe snapshot of current game state."""
        with self.lock:
            if not self.engine or not hasattr(self.engine, 'player'):
                return None
            
            # Get health potion count
            health_potion_count = 0
            for item in self.engine.player.inventory.items:
                if "Health Potion" in item.name:
                    health_potion_count += 1
            
            # Get current messages
            current_messages = []
            if hasattr(self.engine, '_current_step_messages'):
                for msg_data in self.engine._current_step_messages:
                    if msg_data['count'] > 1:
                        current_messages.append(f"{msg_data['text']} ({msg_data['count']} times)")
                    else:
                        current_messages.append(msg_data['text'])
            
            return {
                "dungeon_level": self.engine.game_world.current_floor,
                "current_level_step_count": self.current_level_step_count,
                "message_log": current_messages,
                "player_standing_on": self.engine.get_player_tile_type(),
                "player_health": self.engine.player.fighter.hp,
                "health_potion_count": health_potion_count
            }
    
    def queue_action(self, action_key: str):
        """Queue an action from API to be processed by main game loop."""
        self.action_queue.put(action_key)
    
    def get_screenshot_data(self) -> Optional[bytes]:
        """Get screenshot data thread-safely."""
        with self.lock:
            if not self.renderer or not self.engine:
                return None
            
            try:
                # Render current state to pygame surface
                self.renderer.render_complete(self.engine)
                # Get screenshot as bytes
                return self.renderer.get_screenshot_bytes()
            except Exception as e:
                print(f"Screenshot error: {e}")
                return None

# Global thread-safe game state
game_state = ThreadSafeGameState()

# FastAPI models
class StartGameRequest(BaseModel):
    mode: str = "procedural"
    custom_map: Optional[str] = None  # String representation of the map

class PerformActionRequest(BaseModel):
    action: str

class GameStateResponse(BaseModel):
    dungeon_level: int
    current_level_step_count: int
    message_log: List[str]
    player_standing_on: str
    player_health: int
    health_potion_count: int

class PerformActionResponse(BaseModel):
    action_executed: str
    state_changes: GameStateResponse

# FastAPI app
app = FastAPI(
    title="Roguelike Game API",
    description="API for the roguelike game with pygame rendering",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Roguelike Game API - Pygame Renderer",
        "status": "running" if game_state.engine else "waiting_for_game",
        "renderer": "pygame",
        "tile_size": game_state.renderer.tile_size if game_state.renderer else "unknown"
    }

@app.get("/game-state", response_model=GameStateResponse)
async def get_game_state():
    """
    Retrieve the current game state.
    
    Returns:
    - dungeon_level: Current dungeon level (starts from 1)
    - current_level_step_count: Steps taken on current level (starts from 0, resets each level)
    - message_log: List of new messages since last action
    - player_standing_on: Description of tile player is standing on
    - player_health: Current player health
    - health_potion_count: Number of health potions in inventory
    """
    state = game_state.get_state_snapshot()
    if not state:
        raise HTTPException(status_code=400, detail="No active game session")
    return state

@app.get("/game-info")
async def get_game_info():
    """
    Get information about game entities and items.
    
    Returns a dictionary with entity/item names as keys and objects containing:
    - description: What the entity/item does
    """
    return {
        "Ghost": {
            "description": "A weak enemy that moves towards the player and attacks for moderate damage. Easy to defeat.",
        },
        "Crab": {
            "description": "A stronger enemy with more health and higher attack power. More dangerous than ghosts.",
        },
        "Health Potion": {
            "description": "Restores 4 health points when used. Press 'i' to use automatically.",
        },
        "Stairs/Ladder": {
            "description": "Exit to the next level or complete the game. Press 'space' to use.",
        },
        "Wall": {
            "description": "Solid barrier that blocks movement. Cannot be passed through.",
        },
        "Floor": {
            "description": "Empty walkable space. Player and enemies can move through.",
        }
    }

@app.get("/game-screenshot")
async def get_game_screenshot():
    """
    Capture and return a screenshot of the current game window.
    
    Returns raw binary PNG image data with comprehensive dimension information.
    No resizing - each tile is exactly the configured pixel size.
    
    Headers provide both total screen dimensions and actual game map dimensions.
    """
    screenshot_data = game_state.get_screenshot_data()
    if not screenshot_data:
        raise HTTPException(status_code=400, detail="No active game or failed to capture screenshot")
    
    # Calculate dimensions
    tile_size = game_state.renderer.tile_size if game_state.renderer else 16
    total_width_tiles = game_state.renderer.width if game_state.renderer else 80
    total_height_tiles = game_state.renderer.height if game_state.renderer else 40
    
    # Get actual map dimensions (excluding UI)
    map_width_tiles = 30  # Default fallback
    map_height_tiles = 30  # Default fallback
    
    if game_state.engine and game_state.engine.game_map:
        map_width_tiles = game_state.engine.game_map.width
        map_height_tiles = game_state.engine.game_map.height
    
    return Response(
        content=screenshot_data,
        media_type="image/png",
        headers={
            "Content-Disposition": "inline; filename=game_screenshot.png",
            "X-Tile-Size": str(tile_size),
            "X-Total-Width-Tiles": str(total_width_tiles),
            "X-Total-Height-Tiles": str(total_height_tiles),
            "X-Map-Width-Tiles": str(map_width_tiles),
            "X-Map-Height-Tiles": str(map_height_tiles),
            "X-Total-Width-Pixels": str(total_width_tiles * tile_size),
            "X-Total-Height-Pixels": str(total_height_tiles * tile_size),
            "X-Map-Width-Pixels": str(map_width_tiles * tile_size),
            "X-Map-Height-Pixels": str(map_height_tiles * tile_size)
        }
    )

@app.post("/start-game", response_model=GameStateResponse)
async def start_game(request: StartGameRequest):
    """
    Initialize a new game session.
    
    Parameters:
    - mode: "custom" for predefined map, "procedural" for random generation, "string" for custom string map
    - custom_map: String representation of the map (required when mode is "string")
    
    String map format:
    - '#' = wall
    - '.' = floor  
    - '@' = player starting position
    - '>' = stairs (exit)
    - 'O' = ghost (weak enemy)
    - 'T' = troll/crab (strong enemy)
    - 'h' = health potion
    
    Example:
    ```
    ######
    #@...#
    ####.#
    ####.#
    ####>#
    ######
    ```
    
    Returns the initial game state using the same format as /game-state.
    """
    if request.mode not in ["custom", "procedural", "string"]:
        raise HTTPException(status_code=400, detail="Mode must be 'custom', 'procedural', or 'string'")
    
    if request.mode == "string" and not request.custom_map:
        raise HTTPException(status_code=400, detail="custom_map is required when mode is 'string'")
    
    # Queue a restart action - this will be handled by the main game loop
    if request.mode == "string":
        game_state.queue_action(f"restart_string|{request.custom_map}")
    else:
        game_state.queue_action(f"restart_{request.mode}")
    
    # Wait a moment for the game to restart
    time.sleep(0.1)
    
    state = game_state.get_state_snapshot()
    if not state:
        raise HTTPException(status_code=500, detail="Failed to start game")
    return state

@app.post("/perform-action", response_model=PerformActionResponse)
async def perform_action(request: PerformActionRequest):
    """
    Perform an action in the game by sending key input.
    
    Parameters:
    - action: Key to press. Valid keys:
      - Movement: "w", "a", "s", "d", "up", "down", "left", "right"
      - Actions: "space" (stairs), "g" (pickup), "i" (use health potion)
      - Wait: "." (period) or "wait"
    
    Returns:
    - action_executed: The action that was performed
    - state_changes: Updated game state after the action
    """
    valid_actions = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right', 'space', 'g', 'i', '.', 'wait']
    if request.action.lower() not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
    
    # Queue the action for the main game loop
    game_state.queue_action(request.action.lower())
    
    # Wait a moment for action to be processed
    time.sleep(0.05)
    
    state = game_state.get_state_snapshot()
    if not state:
        raise HTTPException(status_code=400, detail="No active game session")
    
    return {
        "action_executed": request.action,
        "state_changes": state
    }

def run_api_server():
    """Run the FastAPI server in a separate thread."""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def process_api_actions(handler: input_handlers.BaseEventHandler) -> input_handlers.BaseEventHandler:
    """Process any queued API actions."""
    try:
        while not game_state.action_queue.empty():
            action_key = game_state.action_queue.get_nowait()
            
            # Handle restart commands
            if action_key.startswith("restart_"):
                parts = action_key.split("_", 1)
                mode = parts[1]
                
                if mode == "custom":
                    test_map = "custom_map.txt"
                    engine = setup_game.new_game(use_custom_map=True, custom_map_file=test_map)
                elif mode.startswith("string|"):
                    # Extract the custom map string
                    custom_map_string = mode[7:]  # Remove "string|" prefix
                    engine = setup_game.new_game(custom_map_string=custom_map_string)
                else:
                    engine = setup_game.new_game(use_custom_map=False)
                
                new_handler = input_handlers.MainGameEventHandler(engine)
                game_state.set_game_components(engine, new_handler, game_state.renderer)
                game_state.current_level_step_count = 0
                return new_handler
            
            # Handle regular actions
            key_mapping = {
                'w': tcod.event.KeySym.W,
                'a': tcod.event.KeySym.A,
                's': tcod.event.KeySym.S,
                'd': tcod.event.KeySym.D,
                'up': tcod.event.KeySym.UP,
                'down': tcod.event.KeySym.DOWN,
                'left': tcod.event.KeySym.LEFT,
                'right': tcod.event.KeySym.RIGHT,
                'space': tcod.event.KeySym.SPACE,
                'g': tcod.event.KeySym.G,
                'i': tcod.event.KeySym.I,
                '.': tcod.event.KeySym.PERIOD,
                'wait': tcod.event.KeySym.PERIOD,
            }
            
            if action_key in key_mapping:
                # Create and process the key event
                key_event = tcod.event.KeyDown(
                    sym=key_mapping[action_key],
                    mod=tcod.event.Modifier(0),
                    scancode=0
                )
                
                new_handler = handler.handle_events(key_event)
                if new_handler != handler:
                    handler = new_handler
                    game_state.update_handler(handler)
                
                # Update step count for any action
                game_state.current_level_step_count += 1
                print(game_state.current_level_step_count)
    
    except queue.Empty:
        pass
    except Exception as e:
        print(f"Error processing API action: {e}")
    
    return handler

def main() -> None:
    load_dotenv()

    # Initialize pygame renderer
    screen_width = 60
    screen_height = 40
    tile_size = 16  # Exact 16x16 pixels per tile
    
    renderer = PygameRenderer(screen_width, screen_height, tile_size)
    print(f"Pygame renderer initialized: {screen_width}x{screen_height} tiles, {tile_size}x{tile_size} pixels per tile")
    
    # Initialize game
    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("API server started on http://localhost:8000")

    # Initialize global game state
    game_state.set_game_components(None, handler, renderer)
    
    # Main game loop
    clock = pygame.time.Clock()
    
    try:
        while game_state.is_running:
            # Process pygame events
            for event in renderer.handle_events():
                if event.type == pygame.QUIT:
                    game_state.is_running = False
                elif event.type == pygame.KEYDOWN:
                    game_state.current_level_step_count += 1
                    # Convert pygame event to tcod event
                    tcod_event = PygameEventConverter.create_tcod_key_event(event.key, pygame.key.get_mods())
                    if tcod_event:
                        try:
                            new_handler = handler.handle_events(tcod_event)
                            if new_handler != handler:
                                handler = new_handler
                                game_state.update_handler(handler)
                                
                                # Update game state if we have an engine
                                if isinstance(handler, input_handlers.EventHandler) and handler.engine:
                                    game_state.set_game_components(handler.engine, handler, renderer)
                        except Exception as e:
                            print(f"Event handling error: {e}")
                            traceback.print_exc()
            
            # Process any API actions
            handler = process_api_actions(handler)
            
            # Render the game
            try:
                if isinstance(handler, input_handlers.GameDoneEventHandler):
                    # Game completed successfully - render pygame game done screen
                    renderer.render_game_done_screen()
                elif isinstance(handler, input_handlers.GameOverEventHandler):
                    # Player died - render pygame game over screen
                    renderer.render_game_over_screen()
                elif isinstance(handler, input_handlers.EventHandler) and handler.engine:
                    # Game is running - render game state
                    renderer.render_complete(handler.engine)
                elif isinstance(handler, setup_game.MainMenu):
                    # Main menu - render pygame menu
                    renderer.render_main_menu()
                elif hasattr(handler, 'on_render'):
                    # Other handler - clear and show basic state
                    renderer.clear()
                    # For other handlers, could implement pygame versions here
                
                renderer.present()
                
            except Exception as e:
                print(f"Rendering error: {e}")
                traceback.print_exc()
            
            # Control frame rate
            clock.tick(60)  # 60 FPS
            
    except KeyboardInterrupt:
        print("Game interrupted by user")
    except Exception as e:
        print(f"Game error: {e}")
        traceback.print_exc()
    finally:
        game_state.is_running = False
        renderer.quit()
        print("Game closed")

if __name__ == "__main__":
    main()
