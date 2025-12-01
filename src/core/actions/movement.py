from __future__ import annotations

from typing import TYPE_CHECKING

from src.core import color, exceptions
from src.core.actions.base import Action, ActionWithDirection
from src.core.actions.combat import MeleeAction

if TYPE_CHECKING:
    from src.entities import Actor


class MovementAction(ActionWithDirection):
    """Move the entity in the target direction."""
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    """Action that either moves or attacks."""
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class WaitAction(Action):
    """Do nothing for a turn."""
    def perform(self) -> None:
        pass


class TakeStairsAction(Action):
    """Take the stairs down to the next level."""
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            # Check if using custom map
            if self.engine.is_using_custom_map:
                # End game for custom map
                self.engine.message_log.add_message(
                    "You have completed the map! Game Done.", color.welcome_text
                )
                self.engine.game_done = True
                return
            else:
                # Normal behavior for procedural maps
                self.engine.game_world.generate_floor()
                
                # Get new dungeon level for scaling
                new_dungeon_level = self.engine.game_world.current_floor
                
                # Apply dungeon level scaling (increases max HP)
                self.entity.fighter.apply_dungeon_level_scaling(new_dungeon_level)
                
                # Restore 50% of current max health when going to next level
                heal_amount = int(self.entity.fighter.max_hp * 0.5)
                self.entity.fighter.hp = min(
                    self.entity.fighter.hp + heal_amount,
                    self.entity.fighter.max_hp
                )
                
                self.engine.message_log.add_message(
                    "You descend the staircase.", color.descend
                )
                self.engine.message_log.add_message(
                    f"You feel refreshed! Restored {heal_amount} health.", color.health_recovered
                )
        else:
            raise exceptions.Impossible("There are no stairs here.")
