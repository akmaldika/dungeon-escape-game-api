from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap


TParent = TypeVar("TParent", bound="Entity")


class BaseComponent(Generic[TParent]):
    parent: TParent  # Owning entity instance.

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    @property
    def engine(self) -> Engine:
        return self.gamemap.engine
