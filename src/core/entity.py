from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from src.core.render_order import RenderOrder

if TYPE_CHECKING:
	from src.core.components.ai import BaseAI
	from src.core.components.consumable import Consumable
	from src.core.components.fighter import Fighter
	from src.core.components.inventory import Inventory
	from src.core.components.level import Level
	from src.core.game_map import GameMap

T = TypeVar("T", bound="Entity")


class Entity:
	parent: Union[GameMap, "Inventory"]

	def __init__(
		self,
		parent: Optional[GameMap] = None,
		x: int = 0,
		y: int = 0,
		char: str | int = "?",
		color: Tuple[int, int, int] = (255, 255, 255),
		name: str = "<Unnamed>",
		blocks_movement: bool = False,
		render_order: RenderOrder = RenderOrder.CORPSE,
	):
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.name = name
		self.blocks_movement = blocks_movement
		self.render_order = render_order
		if parent:
			self.parent = parent
			parent.entities.add(self)

	@property
	def gamemap(self) -> GameMap:
		return self.parent.gamemap

	def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
		clone = copy.deepcopy(self)
		clone.x = x
		clone.y = y
		clone.parent = gamemap
		gamemap.entities.add(clone)
		return clone

	def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
		self.x = x
		self.y = y
		if gamemap:
			if hasattr(self, "parent"):
				if self.parent is self.gamemap:
					self.gamemap.entities.remove(self)
			self.parent = gamemap
			gamemap.entities.add(self)

	def distance(self, x: int, y: int) -> float:
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

	def move(self, dx: int, dy: int) -> None:
		self.x += dx
		self.y += dy


class Actor(Entity):
	def __init__(
		self,
		*,
		x: int = 0,
		y: int = 0,
		char: str | int = "?",
		color: Tuple[int, int, int] = (255, 255, 255),
		name: str = "<Unnamed>",
		ai_cls: Type[BaseAI],
		fighter: Fighter,
		inventory: "Inventory",
		level: "Level",
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

		self.ai: Optional[BaseAI] = ai_cls(self)

		self.fighter = fighter
		self.fighter.parent = self

		self.inventory = inventory
		self.inventory.parent = self

		self.level = level
		self.level.parent = self

	@property
	def is_alive(self) -> bool:
		return bool(self.fighter and self.fighter.hp > 0)


class Item(Entity):
	def __init__(
		self,
		*,
		x: int = 0,
		y: int = 0,
		char: str | int = "?",
		color: Tuple[int, int, int] = (255, 255, 255),
		name: str = "<Unnamed>",
		consumable: Optional[Consumable] = None,
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

