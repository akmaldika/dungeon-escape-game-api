from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.entity import Entity
from src.entities.render_order import RenderOrder

if TYPE_CHECKING:
    from src.components.ai import BaseAI
    from src.components.fighter import Fighter
    from src.components.inventory import Inventory
    from src.components.level import Level


class Actor(Entity):
    """
    An entity that can perform actions (player, enemies).
    """
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str | int = "?",
        color: tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: type[BaseAI],
        fighter: Fighter,
        inventory: Inventory,
        level: Level,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: BaseAI | None = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.fighter and self.fighter.hp > 0)
