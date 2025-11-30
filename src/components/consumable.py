from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from src.core import actions
from src.core import color
from src.components import ai as components_ai
from src.components import inventory as components_inventory
from src.components.base_component import BaseComponent
from src.core.exceptions import Impossible
from src.core.input_handlers import (
	ActionOrHandler,
)

if TYPE_CHECKING:
	from src.core.entity import Actor, Item


class Consumable(BaseComponent["Item"]):

	def get_action(self, consumer: 'Actor') -> Optional[ActionOrHandler]:
		"""Try to return the action for this item."""
		return actions.ItemAction(consumer, self.parent)

	def activate(self, action: actions.ItemAction) -> None:
		"""Invoke this items ability.

		`action` is the context for this activation.
		"""
		raise NotImplementedError()

	def consume(self) -> None:
		"""Remove the consumed item from its containing inventory."""
		entity = self.parent
		inventory = entity.parent
		if isinstance(inventory, components_inventory.Inventory):
			inventory.items.remove(entity)


class HealingConsumable(Consumable):
	def __init__(self, amount: int):
		self.amount = amount

	def activate(self, action: actions.ItemAction) -> None:
		consumer = action.entity
		amount_recovered = consumer.fighter.heal(self.amount)

		if amount_recovered > 0:
			self.engine.message_log.add_message(
				f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
				color.health_recovered,
			)
			self.consume()
		else:
			raise Impossible(f"Your health is already full.")

