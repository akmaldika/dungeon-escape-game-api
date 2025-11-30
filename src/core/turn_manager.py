from __future__ import annotations

from typing import TYPE_CHECKING

from src.core import exceptions

if TYPE_CHECKING:
    from src.core.engine import Engine

class TurnManager:
    """
    Manages the flow of turns, specifically for enemies.
    """
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_enemy_turns(self) -> None:
        """Handle the turns of all enemies (non-player actors)."""
        for entity in set(self.engine.game_map.actors) - {self.engine.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.
