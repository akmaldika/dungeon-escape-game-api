#!/usr/bin/env python3
"""
Main entrypoint (src/main.py) with pygame rendering and FastAPI server.
Logic unchanged; imports prefer src.* modules.

This file can be run two ways:
- Recommended: from project root -> `py -m src.main`
- Supported: directly -> `py src\main.py` (we insert parent dir into sys.path)
"""

import traceback
import threading
import time
from typing import Optional, Dict, List, Any, Tuple, cast
import queue
import io
from PIL import Image

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

import tcod
import pygame

# Ensure project root is on sys.path when running this file directly
import os, sys
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Prefer src.* modules
from src.app import setup_game  # new src-based module

from src.core import input_handlers  # new src-based core
from src.core.engine import Engine as CoreEngine

from src.rendering.pygame_renderer import PygameRenderer, PygameEventConverter

from src.api.state import ThreadSafeGameState
from src.api.observation import build_observation_payload
from src.api.schemas import (
    StartGameRequest,
    PerformActionRequest,
    GameStateResponse,
    PerformActionResponse,
    ObservationResponse,
)
from src.api.app import create_app
from src.api.config import get_server_settings


game_state = ThreadSafeGameState()
host, port, cors = get_server_settings()
app = create_app(game_state, cors_origins=cors)


@app.get("/game-info")
async def get_game_info():
    tile_size = game_state.renderer.tile_size if game_state.renderer else 16
    def sprite_url(name: str) -> str:
        return f"/sprite/{name}.png"

    dirs = ["w","a","s","d","up","down","left","right"]
    return {
        "Player": {
            "type": "player",
            "capabilities": ["moves", "uses_items"],
            "interactions": [
                {"pickup": "g"},
                {"use_potion": "i"},
                {"wait": "."}
            ],
            "image_url": sprite_url("player"),
            "tile_size": tile_size,
        },
        "Ghost": {
            "type": "enemy",
            "stats": {"health": 10, "power": 2},
            "capabilities": ["hostile", "moves", "attacks_on_bump"],
            "interactions": [
                {"bumpable": dirs},
                {"attackable": dirs}
            ],
            "image_url": sprite_url("ghost"),
            "tile_size": tile_size,
        },
        "Crab": {
            "type": "enemy",
            "stats": {"health": 15, "power": 8},
            "capabilities": ["hostile", "moves", "attacks_on_bump"],
            "interactions": [
                {"bumpable": dirs},
                {"attackable": dirs}
            ],
            "image_url": sprite_url("crab"),
            "tile_size": tile_size,
        },
        "Health Potion": {
            "type": "item",
            "stats": {"heal_amount": 5},
            "capabilities": ["consumable"],
            "interactions": [{"consumable": "i"}],
            "image_url": sprite_url("chest"),
            "tile_size": tile_size,
        },
        "Ladder": {
            "type": "tile",
            "capabilities": ["actionable"],
            "interactions": [{"actionable": "space"}],
            "image_url": sprite_url("ladder"),
            "tile_size": tile_size,
        },
        "Wall": {
            "type": "tile",
            "capabilities": ["blocks_movement"],
            "image_url": sprite_url("wall"),
            "tile_size": tile_size,
        },
        "Floor": {
            "type": "tile",
            "capabilities": ["walkable"],
            "image_url": sprite_url("floor"),
            "tile_size": tile_size,
        },
    }


def run_api_server():
    uvicorn.run(app, host=host, port=port, log_level="info")


def process_api_actions(handler: input_handlers.BaseEventHandler) -> input_handlers.BaseEventHandler:
    try:
        while not game_state.action_queue.empty():
            action_key = game_state.action_queue.get_nowait()
            if action_key.startswith("restart_"):
                parts = action_key.split("_", 1)
                mode = parts[1]
                if mode == "custom":
                    test_map = "custom_map.txt"
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(use_custom_map=True, custom_map_file=test_map))
                elif mode.startswith("string|"):
                    custom_map_string = mode[7:]
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(custom_map_string=custom_map_string))
                else:
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(use_custom_map=False))
                new_handler = input_handlers.MainGameEventHandler(engine)  # type: ignore[arg-type]
                game_state.set_game_components(engine, new_handler, game_state.renderer)
                game_state.current_level_step_count = 0
                game_state.last_known_level = getattr(engine.game_world, 'current_floor', 1)
                game_state.last_known_handler_type = type(new_handler).__name__
                return new_handler

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
            }
            if action_key in key_mapping:
                game_state.check_and_reset_level_steps()
                was_in_game = isinstance(handler, input_handlers.MainGameEventHandler)
                key_event = tcod.event.KeyDown(
                    sym=key_mapping[action_key],
                    mod=tcod.event.Modifier(0),
                    scancode=0
                )
                new_handler = handler.handle_events(key_event)
                if new_handler != handler:
                    handler = new_handler
                    game_state.update_handler(handler)
                if was_in_game and isinstance(handler, input_handlers.MainGameEventHandler):
                    game_state.increment_step_count()
    except queue.Empty:
        pass
    except Exception as e:
        print(f"Error processing API action: {e}")
    return handler


def _build_observation_payload() -> Dict[str, Any]:
    return build_observation_payload(game_state)


@app.get("/observation", response_model=ObservationResponse)
async def observation():
    return _build_observation_payload()


def main() -> None:
    screen_width = 60
    screen_height = 40
    tile_size = 16
    renderer = PygameRenderer(screen_width, screen_height, tile_size)
    print(f"Pygame renderer initialized: {screen_width}x{screen_height} tiles, {tile_size}x{tile_size} pixels per tile")
    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print(f"API server started on http://{host}:{port}")
    game_state.set_game_components(None, handler, renderer)
    clock = pygame.time.Clock()
    try:
        while game_state.is_running:
            for event in renderer.handle_events():
                if event.type == pygame.QUIT:
                    game_state.is_running = False
                elif event.type == pygame.KEYDOWN:
                    game_state.check_and_reset_level_steps()
                    tcod_event = PygameEventConverter.create_tcod_key_event(event.key, pygame.key.get_mods())
                    if tcod_event:
                        try:
                            was_in_game = isinstance(handler, input_handlers.MainGameEventHandler)
                            new_handler = handler.handle_events(tcod_event)
                            if new_handler != handler:
                                handler = new_handler
                                game_state.update_handler(handler)
                            if was_in_game and isinstance(handler, input_handlers.MainGameEventHandler):
                                game_state.increment_step_count()
                            if isinstance(handler, input_handlers.EventHandler) and handler.engine:
                                game_state.set_game_components(handler.engine, handler, renderer)
                        except Exception as e:
                            print(f"Event handling error: {e}")
                            traceback.print_exc()
            handler = process_api_actions(handler)
            try:
                if isinstance(handler, input_handlers.GameDoneEventHandler):
                    renderer.render_game_done_screen()
                elif isinstance(handler, input_handlers.GameOverEventHandler):
                    renderer.render_game_over_screen()
                elif isinstance(handler, input_handlers.EventHandler) and handler.engine:
                    renderer.render_complete(handler.engine)
                elif isinstance(handler, setup_game.MainMenu):
                    renderer.render_main_menu()
                elif hasattr(handler, 'on_render'):
                    renderer.clear()
                renderer.present()
            except Exception as e:
                print(f"Rendering error: {e}")
                traceback.print_exc()
            clock.tick(60)
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
