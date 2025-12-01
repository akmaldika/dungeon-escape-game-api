from src.components.ai import HostileEnemy
from src.components import consumable
from src.components.fighter import Fighter
from src.components.inventory import Inventory
from src.components.level import Level
from src.entities import Actor, Item

from src.core import color

player = Actor(
	char=ord("@"),
	color=color.player,
	name="Player",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=100, base_power=4),
	inventory=Inventory(capacity=26),
	level=Level(),
)

ghost = Actor(
	char=ord("G"),
	color=color.ghost,
	name="Ghost",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=10, base_power=2),
	inventory=Inventory(capacity=0),
	level=Level(),
)

red_ghost = Actor(
	char=ord("R"),
	color=color.red_ghost,
	name="Red Ghost",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=15, base_power=8),
	inventory=Inventory(capacity=0),
	level=Level(),
)

health_potion = Item(
	char=ord("h"),
	color=color.health_potion,
	name="Health Potion",
	consumable=consumable.HealingConsumable(amount=5),
)

