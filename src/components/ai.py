from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING, Optional

import tcod

from src.core.actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction
from src.components.pathfinding import PathfindingService

if TYPE_CHECKING:
    from src.entities.entity import Actor


class BaseAI(Action):
    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """
        Delegate pathfinding to the service.
        """
        return PathfindingService.get_path_to(self.entity, dest_x, dest_y)


class HostileEnemy(BaseAI):
    """
    Standard hostile enemy.
    Chases the player if visible or if it remembers the player's location.
    """
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = abs(dx) + abs(dy)

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                if (abs(dx) == 1 and dy == 0) or (abs(dy) == 1 and dx == 0):
                    return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()


class RelentlessEnemy(BaseAI):
    """
    Relentless enemy.
    Always knows where the player is and chases them, regardless of visibility.
    """
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = abs(dx) + abs(dy)

        # Attack if adjacent
        if distance <= 1:
             if (abs(dx) == 1 and dy == 0) or (abs(dy) == 1 and dx == 0):
                return MeleeAction(self.entity, dx, dy).perform()

        # Always calculate path to player
        self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()


class PatrollingEnemy(BaseAI):
    """
    Patrolling enemy.
    Moves back and forth along a specified axis.
    """
    def __init__(self, entity: Actor, direction: str = "horizontal", steps: int = 5):
        super().__init__(entity)
        self.direction = direction
        self.max_steps = steps
        self.current_steps = 0
        self.moving_positive = True # True = Right/Down, False = Left/Up

    def perform(self) -> None:
        # Determine movement delta based on direction and current state
        dx, dy = 0, 0
        
        if self.direction == "horizontal":
            dx = 1 if self.moving_positive else -1
        elif self.direction == "vertical":
            dy = 1 if self.moving_positive else -1
        else:
            # Default fallback or error handling
            return WaitAction(self.entity).perform()

        dest_x = self.entity.x + dx
        dest_y = self.entity.y + dy

        # Check if move is valid (not blocked)
        if not self.engine.game_map.in_bounds(dest_x, dest_y) or \
           not self.engine.game_map.tiles["walkable"][dest_x, dest_y] or \
           self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            
            # If blocked, flip direction immediately
            self.moving_positive = not self.moving_positive
            self.current_steps = 0
            return WaitAction(self.entity).perform()

        # Perform movement
        try:
            MovementAction(self.entity, dx, dy).perform()
            self.current_steps += 1
            
            # Check if we reached step limit
            if self.current_steps >= self.max_steps:
                self.moving_positive = not self.moving_positive
                self.current_steps = 0
                
        except Exception:
            # If movement fails for some other reason, wait
            return WaitAction(self.entity).perform()
