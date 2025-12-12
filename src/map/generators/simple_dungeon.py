from __future__ import annotations
import random
from typing import Tuple, Iterator, List, TYPE_CHECKING
import tcod

from src.map.generators.base import MapGenerator
from src.map.game_map import GameMap
from src.map import tile_types
from src.map.map_logger import get_map_logger

if TYPE_CHECKING:
    from src.core.engine import Engine


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: "RectangularRoom") -> bool:
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


class SimpleDungeonGenerator(MapGenerator):
    """
    Standard roguelike dungeon generator using rectangular rooms and tunnels.
    Refactored from original procgen.py.
    """

    def generate(self, engine: Engine) -> GameMap:
        player = engine.player
        dungeon = GameMap(
            engine, self.config.map_width, self.config.map_height, entities=[player]
        )

        rooms: List[RectangularRoom] = []
        center_of_last_room = (0, 0)

        for r in range(self.config.max_rooms):
            room_width = random.randint(
                self.config.room_min_size, self.config.room_max_size
            )
            room_height = random.randint(
                self.config.room_min_size, self.config.room_max_size
            )

            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)

            new_room = RectangularRoom(x, y, room_width, room_height)

            if any(new_room.intersects(other_room) for other_room in rooms):
                continue

            # Create walls around the room first
            self._create_room_walls(dungeon, new_room)

            # Then create the floor inside the room
            dungeon.tiles[new_room.inner] = tile_types.floor

            center_of_last_room = new_room.center

            if len(rooms) == 0:
                player.place(*new_room.center, dungeon)
            else:
                # Create tunnels
                self._create_tunnels(dungeon, rooms[-1].center, new_room.center)

            # Spawn entities using the spawner
            self.spawner.spawn_entities(
                new_room, dungeon, engine.game_world.current_floor
            )

            rooms.append(new_room)

        # Place stairs
        if rooms:
            self._place_downstairs(dungeon, center_of_last_room)

        # Log map
        self._log_map(dungeon, engine.game_world.current_floor)

        return dungeon

    def _create_room_walls(self, dungeon: GameMap, room: RectangularRoom) -> None:
        """Mark walls around a room."""
        for x in range(room.x1, room.x2 + 1):
            for y in range(room.y1, room.y2 + 1):
                if x == room.x1 or x == room.x2 or y == room.y1 or y == room.y2:
                    dungeon.tiles[x, y] = tile_types.wall

    def _create_tunnels(
        self, dungeon: GameMap, start: Tuple[int, int], end: Tuple[int, int]
    ) -> None:
        """Create tunnels between two points, including walls around them."""
        for x, y in self._tunnel_coordinates(start, end):
            dungeon.tiles[x, y] = tile_types.floor
            # Add walls around the tunnel
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < dungeon.width
                        and 0 <= ny < dungeon.height
                        and dungeon.tiles[nx, ny] == tile_types.void
                    ):
                        dungeon.tiles[nx, ny] = tile_types.wall

    def _tunnel_coordinates(
        self, start: Tuple[int, int], end: Tuple[int, int]
    ) -> Iterator[Tuple[int, int]]:
        """Return coordinates for an L-shaped tunnel."""
        x1, y1 = start
        x2, y2 = end
        if random.random() < 0.5:
            corner_x, corner_y = x2, y1
        else:
            corner_x, corner_y = x1, y2

        for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
            yield x, y
        for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
            yield x, y

    def _place_downstairs(self, dungeon: GameMap, location: Tuple[int, int]) -> None:
        sx, sy = location
        dungeon.tiles[sx, sy] = tile_types.down_stairs
        dungeon.downstairs_location = (sx, sy)

    def _log_map(self, dungeon: GameMap, floor: int) -> None:
        try:
            map_logger = get_map_logger()
            map_logger.log_map(dungeon, "simple_dungeon", floor)
        except Exception as e:
            print(f"Warning: Failed to log map: {e}")
