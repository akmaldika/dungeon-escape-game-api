from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core import input_handlers
from src.api.services.game_query import GameQueryService

if TYPE_CHECKING:
    from src.core.engine import Engine

class SnapshotBuilder:
    """Service for building game state snapshots."""

    @staticmethod
    def build(engine: Engine | None, handler: input_handlers.BaseEventHandler | None, current_level_step_count: int) -> dict[str, Any] | None:
        """Build a dictionary representation of the current game state."""
        # Only return game state if we have an engine and player; allow done/over screens
        if (not engine or 
            not hasattr(engine, 'player') or 
            not isinstance(handler, (input_handlers.MainGameEventHandler, input_handlers.GameDoneEventHandler, input_handlers.GameOverEventHandler))):
            return None

        # Get health potion count
        health_potion_count = 0
        for item in engine.player.inventory.items:
            if "Health Potion" in item.name:
                health_potion_count += 1

        # Get current messages (stacked: "Text (xN)")
        current_messages: list[str] = []
        if hasattr(engine, '_current_step_messages'):
            for msg_data in engine._current_step_messages:
                count = msg_data.get('count', 1)
                text = msg_data.get('text', '')
                if count > 1:
                    current_messages.append(f"{text} (x{count})")
                else:
                    current_messages.append(text)

        # Termination flags
        is_done = False
        end_reason: str | None = None
        if getattr(engine, 'game_done', False):
            is_done, end_reason = True, 'victory'
        elif not engine.player.is_alive:
            is_done, end_reason = True, 'death'

        # Legal actions based on current state
        legal_actions = GameQueryService.compute_legal_actions(engine)

        return {
            "dungeon_level": engine.game_world.current_floor,
            "current_level_step_count": current_level_step_count,
            "message_log": current_messages,
            "player_standing_on": engine.get_player_tile_type(),
            "player_health": engine.player.fighter.hp,
            "health_potion_count": health_potion_count,
            "player_position": [engine.player.x, engine.player.y],
            "stairs": getattr(engine.game_map, 'downstairs_location', None),
            "is_done": is_done,
            "end_reason": end_reason,
            "legal_actions": legal_actions
        }
