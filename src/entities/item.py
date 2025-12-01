from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.entity import Entity
from src.entities.render_order import RenderOrder

if TYPE_CHECKING:
    from src.components.consumable import Consumable


class Item(Entity):
    """
    An entity that can be picked up and used.
    """
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str | int = "?",
        color: tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: Consumable | None = None,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable

        if self.consumable:
            self.consumable.parent = self
