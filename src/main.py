#!/usr/bin/env python3
"""
Main entrypoint (src/main.py) with pygame rendering and FastAPI server.
"""

import argparse
import signal
import sys
import threading
import traceback
import os

import pygame
import uvicorn

# Ensure project root is on sys.path when running this file directly
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.app import setup_game
from src.app.api_handler import APIActionHandler
from src.core import input_handlers
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


class GameApplication:
    """
    Main game application class.
    Manages the game loop, renderer, API server, and input handling.
    """

    def __init__(self, tile_size: int, port: int, headless: bool):
        self.tile_size = tile_size
        self.port = port
        self.headless = headless
        
        self.screen_width = 60
        self.screen_height = 40
        
        # Initialize Game State
        self.game_state = ThreadSafeGameState()
        self.api_handler = APIActionHandler(self.game_state)
        
        # Initialize Renderer
        self.renderer = PygameRenderer(
            self.screen_width, 
            self.screen_height, 
            self.tile_size, 
            headless=self.headless
        )
        
        # Initialize Input Handler (Main Menu)
        self.handler: input_handlers.BaseEventHandler = setup_game.MainMenu()
        
        # Update Game State
        self.game_state.set_game_components(None, self.handler, self.renderer)
        
        # Initialize API Server
        self.host, _, self.cors = get_server_settings()
        self.app = create_app(self.game_state, cors_origins=self.cors)
        self.api_thread = threading.Thread(target=self._run_api_server, daemon=True)

    def _run_api_server(self) -> None:
        """Run the FastAPI server in a separate thread."""
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        # Disable signal handlers so main thread can handle Ctrl+C
        server.install_signal_handlers = lambda: None
        server.run()

    def start(self) -> None:
        """Start the game application."""
        if self.headless:
            print(f"Pygame renderer initialized in HEADLESS mode")
        else:
            print(f"Pygame renderer initialized: {self.screen_width}x{self.screen_height} tiles, {self.tile_size}x{self.tile_size} pixels per tile")
            
        self.api_thread.start()
        print(f"API server started on http://{self.host}:{self.port}")
        
        clock = pygame.time.Clock()
        
        try:
            while self.game_state.is_running:
                self._handle_events()
                self._process_api_actions()
                self._render()
                clock.tick(60)
        except KeyboardInterrupt:
            print("Game interrupted by user")
        except Exception as e:
            print(f"Game error: {e}")
            traceback.print_exc()
        finally:
            self._cleanup()

    def _handle_events(self) -> None:
        """Handle Pygame events."""
        for event in self.renderer.handle_events():
            if event.type == pygame.QUIT:
                self.game_state.is_running = False
            elif event.type == pygame.KEYDOWN:
                self.game_state.check_and_reset_level_steps()
                tcod_event = PygameEventConverter.create_tcod_key_event(
                    event.key, pygame.key.get_mods()
                )
                if tcod_event:
                    try:
                        was_in_game = isinstance(self.handler, input_handlers.MainGameEventHandler)
                        new_handler = self.handler.handle_events(tcod_event)
                        if new_handler != self.handler:
                            self.handler = new_handler
                            self.game_state.update_handler(self.handler)
                        if was_in_game and isinstance(self.handler, input_handlers.MainGameEventHandler):
                            self.game_state.increment_step_count()
                        if isinstance(self.handler, input_handlers.EventHandler) and self.handler.engine:
                            self.game_state.set_game_components(
                                self.handler.engine, self.handler, self.renderer
                            )
                    except Exception as e:
                        print(f"Event handling error: {e}")
                        traceback.print_exc()

    def _process_api_actions(self) -> None:
        """Process actions from the API."""
        self.handler = self.api_handler.process_actions(self.handler)

    def _render(self) -> None:
        """Render the current game state."""
        try:
            if isinstance(self.handler, input_handlers.GameDoneEventHandler):
                self.renderer.render_game_done_screen()
            elif isinstance(self.handler, input_handlers.GameOverEventHandler):
                self.renderer.render_game_over_screen()
            elif isinstance(self.handler, input_handlers.EventHandler) and self.handler.engine:
                self.renderer.render_complete(self.handler.engine)
            elif isinstance(self.handler, setup_game.MainMenu):
                self.renderer.render_main_menu()
            elif hasattr(self.handler, 'on_render'):
                self.renderer.clear()
            self.renderer.present()
        except Exception as e:
            print(f"Rendering error: {e}")
            traceback.print_exc()

    def _cleanup(self) -> None:
        """Cleanup resources."""
        self.game_state.is_running = False
        self.renderer.quit()
        print("Game closed")


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


def parse_arguments(args: list[str]) -> tuple[int, int, bool]:
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

    # Handle legacy arguments (tile-size=8, port=8001)
    cli_tile_size = known_args.tile_size
    cli_port = known_args.port
    
    for arg in legacy_args:
        if arg.startswith("tile-size="):
            try:
                cli_tile_size = int(arg.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif arg.startswith("port="):
            try:
                cli_port = int(arg.split("=", 1)[1])
            except (ValueError, IndexError):
                pass

    tile_size = _resolve_tile_size_value(cli_tile_size) if cli_tile_size else DEFAULT_SPRITE_SIZE
    port = _resolve_port_value(cli_port) if cli_port else DEFAULT_PORT
    
    headless = known_args.headless or "--headless" in legacy_args or "-h" in legacy_args

    return tile_size, port, headless


def handle_sigint(signum, frame):
    print(f"\nReceived signal {signum}, stopping game...")
    # We can't easily access the game instance here without a global, 
    # but the main loop checks for KeyboardInterrupt too.
    # Ideally, we'd pass a shutdown event or similar.
    sys.exit(0)


def main() -> None:
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    
    tile_size, port, headless = parse_arguments(sys.argv[1:])
    
    app = GameApplication(tile_size, port, headless)
    app.start()


if __name__ == "__main__":
    main()
