from __future__ import annotations

from typing import TYPE_CHECKING

from src.core import color, exceptions
from src.core.actions.base import ActionWithDirection

if TYPE_CHECKING:
    from src.entities import Actor


class MeleeAction(ActionWithDirection):
    """Attack an entity in the target direction."""
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.fighter.power

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.take_damage(damage)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
