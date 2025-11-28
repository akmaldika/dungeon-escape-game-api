from __future__ import annotations

from typing import Optional, Dict, List, Any, Tuple
import threading
import queue

import tcod  # type: ignore
try:
    from src.core import input_handlers  # prefer src version
except Exception:
    import input_handlers  # fallback during migration


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

    def get_state_snapshot(self):
        """Get thread-safe snapshot of current game state for API responses."""
        with self.lock:
            # Only return game state if we have an engine and player; allow done/over screens
            if (not self.engine or 
                not hasattr(self.engine, 'player') or 
                not isinstance(self.handler, (input_handlers.MainGameEventHandler, input_handlers.GameDoneEventHandler, input_handlers.GameOverEventHandler))):
                return None

            # Get health potion count
            health_potion_count = 0
            for item in self.engine.player.inventory.items:
                if "Health Potion" in item.name:
                    health_potion_count += 1

            # Get current messages (stacked: "Text (xN)")
            current_messages: List[str] = []
            if hasattr(self.engine, '_current_step_messages'):
                for msg_data in self.engine._current_step_messages:
                    count = msg_data.get('count', 1)
                    text = msg_data.get('text', '')
                    if count > 1:
                        current_messages.append(f"{text} (x{count})")
                    else:
                        current_messages.append(text)

            # Termination flags
            is_done = False
            end_reason: Optional[str] = None
            if getattr(self.engine, 'game_done', False):
                is_done, end_reason = True, 'victory'
            elif not self.engine.player.is_alive:
                is_done, end_reason = True, 'death'

            # Legal actions based on current state
            legal_actions = compute_legal_actions_unlocked(self.engine)

            return {
                "dungeon_level": self.engine.game_world.current_floor,
                "current_level_step_count": self.current_level_step_count,
                "message_log": current_messages,
                "player_standing_on": self.engine.get_player_tile_type(),
                "player_health": self.engine.player.fighter.hp,
                "health_potion_count": health_potion_count,
                "player_position": [self.engine.player.x, self.engine.player.y],
                "stairs": getattr(self.engine.game_map, 'downstairs_location', None),
                "is_done": is_done,
                "end_reason": end_reason,
                "legal_actions": legal_actions
            }

    def queue_action(self, action_key: str):
        """Queue an action from API to be processed by main game loop."""
        self.action_queue.put(action_key)

    def get_screenshot_data(self) -> Optional[bytes]:
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


# ---------------- Helper utilities for API state -----------------
def _on_stairs(engine) -> bool:
    if not engine or not hasattr(engine, 'game_map'):
        return False
    px, py = engine.player.x, engine.player.y
    stairs = getattr(engine.game_map, 'downstairs_location', None)
    if not stairs:
        return False
    sx, sy = stairs
    dx = abs(px - sx)
    dy = abs(py - sy)
    # True only if on the stairs tile (no adjacency)
    return (dx == 0 and dy == 0)


def _has_item_underfoot(engine) -> bool:
    if not engine or not hasattr(engine, 'game_map'):
        return False
    px, py = engine.player.x, engine.player.y
    for it in engine.game_map.items:
        if it.x == px and it.y == py:
            return True
    return False


def _has_potion(engine) -> bool:
    if not engine:
        return False
    # Check if player has health potion AND health is not at maximum
    if engine.player.fighter.hp >= engine.player.fighter.max_hp:
        return False
    for it in engine.player.inventory.items:
        if getattr(it, 'consumable', None) and 'Health Potion' in it.name:
            return True
    return False


def _can_bump(engine, dx: int, dy: int) -> bool:
    gm = getattr(engine, 'game_map', None)
    if gm is None:
        return False
    x = engine.player.x + dx
    y = engine.player.y + dy
    if not gm.in_bounds(x, y):
        return False
    # If there is an actor there, bump (attack) is allowed
    if gm.get_actor_at_location(x, y) is not None:
        return True
    # Otherwise require walkable tile
    return bool(gm.tiles['walkable'][x, y])


def compute_legal_actions_unlocked(engine) -> List[str]:
    """Compute legal action keys based on current engine state.
    Returns keys from set: w/a/s/d, g, i, space, .
    """
    if not engine or not hasattr(engine, 'player'):
        return []
    legal: List[str] = []
    # Movement in 4 directions (bump into enemies or walk on floor)
    dirs = {
        'w': (0, -1),
        's': (0, 1),
        'a': (-1, 0),
        'd': (1, 0),
    }
    for k, (dx, dy) in dirs.items():
        if _can_bump(engine, dx, dy):
            legal.append(k)
    if _has_item_underfoot(engine):
        legal.append('g')
    if _has_potion(engine):
        legal.append('i')
    if _on_stairs(engine):
        legal.append('space')
    legal.append('.')  # wait always allowed
    # Add UI-level keys for non-gameplay states (allow returning to menu)
    if getattr(engine, 'game_done', False) or not engine.player.is_alive:
        legal.append('esc')
        legal.append('q')
    # Dedupe preserve order
    seen = set()
    result: List[str] = []
    for a in legal:
        if a not in seen:
            seen.add(a)
            result.append(a)
    return result


__all__ = [
    "ThreadSafeGameState",
    "compute_legal_actions_unlocked",
]
