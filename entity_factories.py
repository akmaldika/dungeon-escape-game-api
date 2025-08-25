from components.ai import HostileEnemy
from components import consumable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

import os
from dotenv import load_dotenv
load_dotenv()

player = Actor(
    char= 0x100000 if os.getenv("IS_USE_GRAPHIC") == "1" or True else "@",
    # color=(255, 255, 255),
    color=(71, 108, 108),
    name="Player",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=100, base_defense=1, base_power=4),
    inventory=Inventory(capacity=26),
    level=Level(),
)

ghost = Actor(
    char= 0x100001 if os.getenv("IS_USE_GRAPHIC") == "1" or True else "O",
    # color=(63, 127, 63),
    color=(71, 108, 108),
    name="Ghost",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(),
)

troll = Actor(
    char= 0x100002 if os.getenv("IS_USE_GRAPHIC") == "1" or True else "T",
    # color=(0, 127, 0),
    color=(71, 108, 108),
    name="Crab",
    ai_cls=HostileEnemy,

    fighter=Fighter(hp=15, base_defense=0, base_power=8),
    inventory=Inventory(capacity=0),
    level=Level(),
)

health_potion = Item(
    char=0x100008 if True else "h",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=5),
)

