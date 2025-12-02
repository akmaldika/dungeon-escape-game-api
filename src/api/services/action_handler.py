"""
API Action Handler.

This module processes actions queued by the API and applies them to the game state.
"""

from __future__ import annotations

import queue
from typing import cast, TYPE_CHECKING

import tcod

from src.core import input_handlers
from src.api.state import ThreadSafeGameState

if TYPE_CHECKING:
    from src.core.engine import Engine

class APIActionHandler:
    """Handles processing of API actions."""

    def __init__(self, game_state: ThreadSafeGameState):
        self.game_state = game_state
        self.key_mapping = {
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

    def process_actions(self, handler: input_handlers.BaseEventHandler) -> input_handlers.BaseEventHandler:
        """Process all pending actions in the queue."""
        try:
            while not self.game_state.action_queue.empty():
                action_key = self.game_state.action_queue.get_nowait()
                
                # Handle restart commands
                if action_key.startswith("restart_"):
                    return self._handle_restart(action_key)

                # Handle key commands
                if action_key in self.key_mapping:
                    handler = self._handle_key_action(action_key, handler)
                    
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing API action: {e}")
            
        return handler

    def _handle_restart(self, action_key: str) -> input_handlers.BaseEventHandler:
        """Handle game restart commands."""
        # Import here to avoid circular imports
        from src.core.setup import create_game_from_mode
        
        parts = action_key.split("_", 1)
        mode_string = parts[1]
        
        engine = create_game_from_mode(mode_string)
            
        new_handler = input_handlers.MainGameEventHandler(engine)
        self.game_state.set_game_components(engine, new_handler, self.game_state.renderer)
        self.game_state.current_level_step_count = 0
        self.game_state.last_known_level = getattr(engine.game_world, 'current_floor', 1)
        self.game_state.last_known_handler_type = type(new_handler).__name__
        return new_handler

    def _handle_key_action(self, action_key: str, handler: input_handlers.BaseEventHandler) -> input_handlers.BaseEventHandler:
        """Handle keyboard action simulation."""
        self.game_state.check_and_reset_level_steps()
        was_in_game = isinstance(handler, input_handlers.MainGameEventHandler)
        
        key_event = tcod.event.KeyDown(
            sym=self.key_mapping[action_key],
            mod=tcod.event.Modifier(0),
            scancode=0
        )
        
        new_handler = handler.handle_events(key_event)
        
        if new_handler != handler:
            handler = new_handler
            self.game_state.update_handler(handler)
            
        if was_in_game and isinstance(handler, input_handlers.MainGameEventHandler):
            self.game_state.increment_step_count()
            
        return handler
