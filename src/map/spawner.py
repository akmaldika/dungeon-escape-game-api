from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, TYPE_CHECKING
from src.entities import entity_factories

if TYPE_CHECKING:
    from src.map.game_map import GameMap
    from src.entities.entity import Entity
    from src.map.room import RectangularRoom


class EntitySpawner(ABC):
    """Abstract base class for entity spawning strategies."""

    @abstractmethod
    def spawn_entities(
        self, room: "RectangularRoom", dungeon: GameMap, floor_number: int
    ) -> None:
        pass


class RandomTableSpawner(EntitySpawner):
    """Spawns entities based on weighted chance tables (classic roguelike)."""

    def __init__(self):
        # Configuration could be moved to init, but hardcoded for now to match procgen.py
        self.max_items_by_floor = [
            (1, 1),
            (4, 2),
        ]
        self.max_monsters_by_floor = [
            (1, 2),
            (4, 3),
            (6, 5),
        ]
        self.item_chances = {
            0: [(entity_factories.health_potion, 35)],
            2: [(entity_factories.health_potion, 35)],
            4: [(entity_factories.health_potion, 35)],
            6: [(entity_factories.health_potion, 35)],
        }
        self.enemy_chances = {
            0: [(entity_factories.ghost, 80)],
            3: [(entity_factories.red_ghost, 15)],
            5: [(entity_factories.red_ghost, 30)],
            7: [(entity_factories.red_ghost, 60)],
        }

    def _get_max_value_for_floor(
        self, max_value_by_floor: List[Tuple[int, int]], floor: int
    ) -> int:
        current_value = 0
        for floor_minimum, value in max_value_by_floor:
            if floor_minimum > floor:
                break
            else:
                current_value = value
        return current_value

    def _get_entities_at_random(
        self,
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        number_of_entities: int,
        floor: int,
    ) -> List[Entity]:
        entity_weighted_chances = {}

        for key, values in weighted_chances_by_floor.items():
            if key > floor:
                break
            else:
                for value in values:
                    entity = value[0]
                    weighted_chance = value[1]
                    entity_weighted_chances[entity] = weighted_chance

        entities = list(entity_weighted_chances.keys())
        entity_weighted_chance_values = list(entity_weighted_chances.values())

        if not entities:
            return []

        chosen_entities = random.choices(
            entities, weights=entity_weighted_chance_values, k=number_of_entities
        )
        return chosen_entities

    def spawn_entities(
        self, room: "RectangularRoom", dungeon: GameMap, floor_number: int
    ) -> None:
        number_of_monsters = random.randint(
            0, self._get_max_value_for_floor(self.max_monsters_by_floor, floor_number)
        )
        number_of_items = random.randint(
            0, self._get_max_value_for_floor(self.max_items_by_floor, floor_number)
        )

        monsters = self._get_entities_at_random(
            self.enemy_chances, number_of_monsters, 0
        )
        items = self._get_entities_at_random(
            self.item_chances, number_of_items, floor_number
        )

        for entity in monsters + items:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)

            if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
                entity.spawn(dungeon, x, y)
