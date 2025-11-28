from components.ai import HostileEnemy
from components import consumable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char=0x100000,
    # color=(255, 255, 255),
    color=(71, 108, 108),
    name="Player",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=100, base_power=4),
    inventory=Inventory(capacity=26),
    level=Level(),
)

# Enemies

ghost = Actor(
    char=0x100001,
    # color=(63, 127, 63),
    color=(71, 108, 108),
    name="Ghost",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=10, base_power=2),
    inventory=Inventory(capacity=0),
    level=Level(),
)

red_ghost = Actor(
    char=0x100002,
    # color=(0, 127, 0),
    color=(71, 108, 108),
    name="Red Ghost",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=15, base_power=8),
    inventory=Inventory(capacity=0),
    level=Level(),
)

# Items

health_potion = Item(
    char=0x100008,
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=5),
)

