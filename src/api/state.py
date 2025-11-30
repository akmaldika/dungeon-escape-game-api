from __future__ import annotations

from typing import Optional, Dict, List, Any, Tuple
import threading
import queue

import tcod  # type: ignore
from src.core import input_handlers
from src.api.services.snapshot_builder import SnapshotBuilder


class ThreadSafeGameState:
    def __init__(self):
        self.lock = threading.Lock()
        self.engine = None  # Type: Engine
        self.handler: Optional[input_handlers.BaseEventHandler] = None
        self.renderer = None  # Late-bound PygameRenderer
        self.current_level_step_count = 0
        self.last_known_level = 1  # Track current dungeon level
        self.last_known_handler_type = None  # Track handler type for resets
        self.is_running = True
        self.action_queue: "queue.Queue[str]" = queue.Queue()  # For API actions

    def set_game_components(self, engine, handler, renderer):
        with self.lock:
            self.engine = engine
            self.handler = handler
            self.renderer = renderer

    def update_handler(self, new_handler):
        with self.lock:
            self.handler = new_handler
            # Reset step count when changing handler types (game state changes)
            handler_type = type(new_handler).__name__
            if self.last_known_handler_type != handler_type:
                self.current_level_step_count = 0
                self.last_known_handler_type = handler_type

    def check_and_reset_level_steps(self):
        """Check if we've moved to a new level and reset step count if so."""
        with self.lock:
            if self.engine and hasattr(self.engine, 'game_world'):
                current_level = getattr(self.engine.game_world, 'current_floor', 1)
                if current_level != self.last_known_level:
                    self.current_level_step_count = 0
                    self.last_known_level = current_level

    def increment_step_count(self):
        """Safely increment the step count for the current level."""
        with self.lock:
            self.current_level_step_count += 1

    def get_state_snapshot(self) -> dict[str, Any] | None:
        """Get thread-safe snapshot of current game state for API responses."""
        with self.lock:
            return SnapshotBuilder.build(self.engine, self.handler, self.current_level_step_count)

    def queue_action(self, action_key: str):
        """Queue an action from API to be processed by main game loop."""
        self.action_queue.put(action_key)

    def get_screenshot_data(self) -> bytes | None:
        """Get screenshot data thread-safely from the renderer."""
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
