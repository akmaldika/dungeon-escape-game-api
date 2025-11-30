from __future__ import annotations

from typing import List, TYPE_CHECKING

from src.components.base_component import BaseComponent

if TYPE_CHECKING:
	from src.core.entity import Actor, Item


class Inventory(BaseComponent["Actor"]):

	def __init__(self, capacity: int):
		self.capacity = capacity
		self.items: List['Item'] = []

	def drop(self, item: 'Item') -> None:
		self.items.remove(item)
		item.place(self.parent.x, self.parent.y, self.gamemap)

		self.engine.message_log.add_message(f"You dropped the {item.name}.")

