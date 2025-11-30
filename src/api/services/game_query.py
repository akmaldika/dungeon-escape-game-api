from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.engine import Engine

class GameQueryService:
    """Service for querying specific game states and conditions."""

    @staticmethod
    def on_stairs(engine: Engine | None) -> bool:
        """Check if the player is standing on the stairs."""
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

    @staticmethod
    def has_item_underfoot(engine: Engine | None) -> bool:
        """Check if there is an item at the player's location."""
        if not engine or not hasattr(engine, 'game_map'):
            return False
        px, py = engine.player.x, engine.player.y
        for it in engine.game_map.items:
            if it.x == px and it.y == py:
                return True
        return False

    @staticmethod
    def has_potion(engine: Engine | None) -> bool:
        """Check if the player has a health potion and needs it."""
        if not engine:
            return False
        # Check if player has health potion AND health is not at maximum
        if engine.player.fighter.hp >= engine.player.fighter.max_hp:
            return False
        for it in engine.player.inventory.items:
            if getattr(it, 'consumable', None) and 'Health Potion' in it.name:
                return True
        return False

    @staticmethod
    def can_bump(engine: Engine | None, dx: int, dy: int) -> bool:
        """Check if the player can move or attack in the given direction."""
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

    @staticmethod
    def compute_legal_actions(engine: Engine | None) -> list[str]:
        """Compute legal action keys based on current engine state.
        Returns keys from set: w/a/s/d, g, i, space, .
        """
        if not engine or not hasattr(engine, 'player'):
            return []
        legal: list[str] = []
        # Movement in 4 directions (bump into enemies or walk on floor)
        dirs = {
            'w': (0, -1),
            's': (0, 1),
            'a': (-1, 0),
            'd': (1, 0),
        }
        for k, (dx, dy) in dirs.items():
            if GameQueryService.can_bump(engine, dx, dy):
                legal.append(k)
        if GameQueryService.has_item_underfoot(engine):
            legal.append('g')
        if GameQueryService.has_potion(engine):
            legal.append('i')
        if GameQueryService.on_stairs(engine):
            legal.append('space')
        legal.append('.')  # wait always allowed
        # Add UI-level keys for non-gameplay states (allow returning to menu)
        if getattr(engine, 'game_done', False) or not engine.player.is_alive:
            legal.append('esc')
            legal.append('q')
        
        # Dedupe preserve order
        seen = set()
        result: list[str] = []
        for a in legal:
            if a not in seen:
                seen.add(a)
                result.append(a)
        return result
