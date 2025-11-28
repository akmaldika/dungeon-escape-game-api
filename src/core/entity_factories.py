from src.core.components.ai import HostileEnemy
from src.core.components import consumable
from src.core.components.fighter import Fighter
from src.core.components.inventory import Inventory
from src.core.components.level import Level
from src.core.entity import Actor, Item

player = Actor(
	char=0x100000,
	color=(71, 108, 108),
	name="Player",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=100, base_power=4),
	inventory=Inventory(capacity=26),
	level=Level(),
)

ghost = Actor(
	char=0x100001,
	color=(71, 108, 108),
	name="Ghost",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=10, base_power=2),
	inventory=Inventory(capacity=0),
	level=Level(),
)

troll = Actor(
	char=0x100002,
	color=(71, 108, 108),
	name="Red Ghost",
	ai_cls=HostileEnemy,
	fighter=Fighter(hp=15, base_power=8),
	inventory=Inventory(capacity=0),
	level=Level(),
)

health_potion = Item(
	char=0x100008,
	color=(127, 0, 255),
	name="Health Potion",
	consumable=consumable.HealingConsumable(amount=5),
)

