from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from src.core import actions
from src.core import color
from src.components import inventory as components_inventory
from src.components.base_component import BaseComponent
from src.core.exceptions import Impossible

if TYPE_CHECKING:
    from src.entities.entity import Actor, Item
    from src.core.input_handlers import ActionOrHandler


class Consumable(BaseComponent["Item"], ABC):
    """
    Abstract base class for consumable items.
    """

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return actions.ItemAction(consumer, self.parent)

    @abstractmethod
    def activate(self, action: actions.ItemAction) -> None:
        """
        Invoke this item's ability.
        
        Args:
            action: The context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components_inventory.Inventory):
            inventory.items.remove(entity)


class HealingConsumable(Consumable):
    """
    Consumable that heals the consumer.
    """
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
