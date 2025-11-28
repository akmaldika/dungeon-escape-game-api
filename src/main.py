#!/usr/bin/env python3
"""
Main entrypoint (src/main.py) with pygame rendering and FastAPI server.
Logic unchanged; imports prefer src.* modules.

This file can be run two ways:
- Recommended: from project root -> `py -m src.main`
- Supported: directly -> `py src/main.py` (we insert parent dir into sys.path)

Command-line arguments:
- tile-size=8 or tile-size=16 (default: 16)
  Example: python src/main.py tile-size=8
  
- port=8000-65535 (default: 8000)
  Example: python src/main.py port=8001
  
Combined example:
  python src/main.py tile-size=8 port=8001
"""

import traceback
import threading
import time
from typing import Optional, Dict, List, Any, Tuple, cast
import queue
import io
import argparse
from PIL import Image

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

import tcod
import pygame

# Ensure project root is on sys.path when running this file directly
import os, sys
import signal

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

from src.api.app import create_app
from src.api.config import get_server_settings
from src.api.sprite_config import (
    DEFAULT_SPRITE_SIZE,
    SUPPORTED_SPRITE_SIZES,
    validate_sprite_directory,
)
from src.api.port_config import (
    DEFAULT_PORT,
    MIN_PORT,
    MAX_PORT,
    validate_port,
    is_port_available,
)


game_state = ThreadSafeGameState()
# Initialize with defaults; will be updated in main()
host, port, cors = get_server_settings()
app = create_app(game_state, cors_origins=cors)





def run_api_server():
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    # Disable signal handlers so main thread can handle Ctrl+C
    server.install_signal_handlers = lambda: None
    server.run()


def process_api_actions(handler: input_handlers.BaseEventHandler) -> input_handlers.BaseEventHandler:
    try:
        while not game_state.action_queue.empty():
            action_key = game_state.action_queue.get_nowait()
            if action_key.startswith("restart_"):
                parts = action_key.split("_", 1)
                mode = parts[1]
                if mode.startswith("custom|"):
                    # Parse custom mode with FOV: "custom|partial,8"
                    fov_parts = mode[7:].split(",") if "|" in mode else ["partial", "8"]
                    fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
                    fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
                    test_map = "custom_map.txt"
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(
                        use_custom_map=True, custom_map_file=test_map,
                        fov_mode=fov_mode, fov_radius=fov_radius
                    ))
                elif mode == "custom":
                    # Fallback for old format
                    test_map = "custom_map.txt"
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(use_custom_map=True, custom_map_file=test_map))
                elif mode.startswith("string|"):
                    # Parse string mode: "string|map_data|partial,8"
                    parts = mode[7:].split("|")
                    custom_map_string = parts[0]
                    if len(parts) > 1:
                        fov_parts = parts[1].split(",")
                        fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
                        fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
                    else:
                        fov_mode, fov_radius = "partial", 8
                    engine: CoreEngine = cast(CoreEngine, setup_game.new_game(
                        custom_map_string=custom_map_string,
                        fov_mode=fov_mode, fov_radius=fov_radius
                    ))
                elif mode.startswith("procedural|"):
                    # Parse procedural parameters: "procedural|30,4,6,30,30,partial,8"
                    param_string = mode[11:]  # Remove "procedural|"
                    try:
                        parts = param_string.split(",")
                        max_rooms, room_min_size, room_max_size, map_width, map_height = map(int, parts[:5])
                        fov_mode = parts[5] if len(parts) > 5 else "partial"
                        fov_radius = int(parts[6]) if len(parts) > 6 else 8
                        engine: CoreEngine = cast(CoreEngine, setup_game.new_game(
                            use_custom_map=False,
                            max_rooms=max_rooms,
                            room_min_size=room_min_size,
                            room_max_size=room_max_size,
                            map_width=map_width,
                            map_height=map_height,
                            fov_mode=fov_mode,
                            fov_radius=fov_radius
                        ))
                    except (ValueError, TypeError):
                        # Fallback to defaults if parsing fails
                        engine: CoreEngine = cast(CoreEngine, setup_game.new_game(use_custom_map=False))
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
                'esc': tcod.event.KeySym.ESCAPE,
                'q': tcod.event.KeySym.Q,
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





def _resolve_port_value(port_val: int) -> int:
    is_valid, msg = validate_port(port_val)
    if not is_valid:
        print(f"Error: Invalid port {port_val}. {msg}")
        print(f"       Valid range: {MIN_PORT}-{MAX_PORT}")
        sys.exit(1)

    if msg:
        print(msg)

    if not is_port_available(port_val):
        print(f"Error: Port {port_val} is already in use.")
        print(f"       Try a different port (e.g., port={port_val + 1})")
        sys.exit(1)

    print(f"Using port {port_val}")
    return port_val


def _resolve_tile_size_value(size: int) -> int:
    if size not in SUPPORTED_SPRITE_SIZES:
        print(
            f"Error: Unsupported tile size {size}. "
            f"Supported sizes: {SUPPORTED_SPRITE_SIZES}"
        )
        sys.exit(1)

    if not validate_sprite_directory(size):
        print(
            f"Error: Sprite directory for {size}px not found. "
            f"Available sprite directories: {SUPPORTED_SPRITE_SIZES}"
        )
        sys.exit(1)

    print(f"Using {size}px sprites")
    return size


def parse_port(args: List[str], cli_value: Optional[int] = None) -> int:
    """Parse port from command-line arguments.

    Supports two formats:
    - Flag style: --port 8001 / -p 8001 (handled via cli_value)
    - Legacy style: port=8001
    """
    if cli_value is not None:
        return _resolve_port_value(cli_value)

    for arg in args:
        if arg.startswith("port="):
            try:
                port_val = int(arg.split("=", 1)[1])
                return _resolve_port_value(port_val)
            except (ValueError, IndexError):
                print(f"Error: Invalid port format. Use: --port 8001 or port=8001")
                sys.exit(1)

    return DEFAULT_PORT


def parse_tile_size(args: List[str], cli_value: Optional[int] = None) -> int:
    """Parse tile-size from command-line arguments.

    Supports two formats:
    - Flag style: --tile-size 8 / -t 8 (handled via cli_value)
    - Legacy style: tile-size=8
    """
    if cli_value is not None:
        return _resolve_tile_size_value(cli_value)

    for arg in args:
        if arg.startswith("tile-size="):
            try:
                size = int(arg.split("=", 1)[1])
                return _resolve_tile_size_value(size)
            except (ValueError, IndexError):
                print(f"Error: Invalid tile-size format. Use: --tile-size 8 or tile-size=8")
                sys.exit(1)

    return DEFAULT_SPRITE_SIZE


def parse_arguments(args: List[str]) -> Tuple[int, int, bool]:
    parser = argparse.ArgumentParser(
        description="Configure the roguelike renderer and API server",
        add_help=True,
        allow_abbrev=False,
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        help=f"API port between {MIN_PORT} and {MAX_PORT} (default {DEFAULT_PORT})",
    )
    parser.add_argument(
        "-t", "--tile-size",
        type=int,
        choices=list(SUPPORTED_SPRITE_SIZES),
        help=f"Tile size in pixels (default {DEFAULT_SPRITE_SIZE})",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no window) for AI benchmarking",
    )

    known_args, legacy_args = parser.parse_known_args(args)

    tile_size = parse_tile_size(legacy_args, cli_value=known_args.tile_size)
    port = parse_port(legacy_args, cli_value=known_args.port)
    
    # Check for headless flag in remaining args or known args
    headless = "--headless" in args or "-h" in args # Simple check for now, or better:
    
    return tile_size, port, known_args.headless


def handle_sigint(signum, frame):
    print(f"\nReceived signal {signum}, stopping game...")
    game_state.is_running = False


def main() -> None:
    global host, port  # Update global port for run_api_server
    
    # Parse command-line arguments for tile size and port
    tile_size, port, headless = parse_arguments(sys.argv[1:])

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    
    screen_width = 60
    screen_height = 40
    renderer = PygameRenderer(screen_width, screen_height, tile_size, headless=headless)
    if headless:
        print(f"Pygame renderer initialized in HEADLESS mode")
    else:
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
