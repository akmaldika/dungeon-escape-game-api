from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.engine import Engine
    from src.map.game_map import GameMap
    from src.map.configuration import MapConfiguration
    from src.map.spawner import EntitySpawner


class MapGenerator(ABC):
    """Abstract base class for map generators."""

    def __init__(self, map_config: MapConfiguration, spawner: EntitySpawner):
        self.config = map_config
        self.spawner = spawner

    @abstractmethod
    def generate(self, engine: Engine) -> GameMap:
        """Generate a new GameMap."""
        pass
