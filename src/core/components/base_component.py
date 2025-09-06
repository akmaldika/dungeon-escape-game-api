from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

if TYPE_CHECKING:
	from src.core.engine import Engine
	from src.core.entity import Entity
	from src.core.game_map import GameMap


TParent = TypeVar("TParent", bound="Entity")


class BaseComponent(Generic[TParent]):
	parent: TParent

	@property
	def gamemap(self) -> GameMap:
		return self.parent.gamemap

	@property
	def engine(self) -> Engine:
		return self.gamemap.engine

