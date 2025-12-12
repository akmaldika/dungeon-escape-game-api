from __future__ import annotations

from typing import Iterable, Iterator, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console
from tcod import libtcodpy

from src.entities import Actor, Item
from src.map import tile_types

if TYPE_CHECKING:
    from src.core.engine import Engine
    from src.entities.entity import Entity


class GameMap:
    """
    The game map, which holds tiles and entities.
    """

    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.void, order="F")

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before

        self.downstairs_location: tuple[int, int] = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        """Iterate over this maps items."""
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self,
        location_x: int,
        location_y: int,
    ) -> Entity | None:
        """Return the blocking entity at a location, if any."""
        for entity in self.entities:
            if (
                getattr(entity, "blocks_movement", False)
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity
        return None

    def get_actor_at_location(self, x: int, y: int) -> Actor | None:
        """Return the actor at a location, if any."""
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".
        """
        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x, entity.y]:
                libtcodpy.console_put_char(
                    con=console,
                    x=entity.x,
                    y=entity.y,
                    c=entity.char,
                    flag=libtcodpy.BKGND_NONE,
                )


class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0,
        map_gen_type: str = "dungeon",
    ):
        from src.map.configuration import MapConfiguration

        self.engine = engine
        self.current_floor = current_floor
        self.map_gen_type = map_gen_type

        # Create configuration object from legacy arguments
        self.config = MapConfiguration(
            map_width=map_width,
            map_height=map_height,
            max_rooms=max_rooms,
            room_min_size=room_min_size,
            room_max_size=room_max_size,
        )

    def generate_floor(self) -> None:
        """Generate a new floor and update the engine's game map."""
        from src.map.spawner import RandomTableSpawner
        from src.map.generators.simple_dungeon import SimpleDungeonGenerator
        from src.map.generators.cellular import CellularAutomataGenerator

        self.current_floor += 1

        # Use new modular system
        spawner = RandomTableSpawner()

        if self.map_gen_type == "cellular":
            generator = CellularAutomataGenerator(self.config, spawner)
        else:
            generator = SimpleDungeonGenerator(self.config, spawner)

        self.engine.game_map = generator.generate(self.engine)
