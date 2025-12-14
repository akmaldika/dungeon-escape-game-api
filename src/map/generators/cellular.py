from __future__ import annotations
import random
import copy
from typing import List, Tuple, TYPE_CHECKING
import tcod

from src.map.generators.base import MapGenerator
from src.map.game_map import GameMap
from src.map import tile_types
from src.map.map_logger import get_map_logger

if TYPE_CHECKING:
    from src.core.engine import Engine


class CellularAutomataGenerator(MapGenerator):
    """
    Generates cave-like maps using cellular automata.
    """

    def generate(self, engine: Engine) -> GameMap:
        player = engine.player
        dungeon = GameMap(
            engine, self.config.map_width, self.config.map_height, entities=[player]
        )

        # 1. Randomize map with 45% walls
        colors = []
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                if random.random() < 0.45:
                    dungeon.tiles[x, y] = tile_types.wall
                else:
                    dungeon.tiles[x, y] = tile_types.floor

        # 2. Smooth map (Cellular Automata steps)
        # 5 steps usually makes nice smooth caves
        for _ in range(5):
            self._smooth_map(dungeon)

        # 3. Ensure connectivity (Flood fill)
        # Find largest cavern and fill others
        largest_cavern = self._get_largest_cavern(dungeon)

        # Fill everything that is NOT in the largest cavern
        for y in range(dungeon.height):
            for x in range(dungeon.width):
                if (x, y) not in largest_cavern:
                    dungeon.tiles[x, y] = tile_types.wall

        # 3b. Enforce Borders (Make edges walls)
        for x in range(dungeon.width):
            dungeon.tiles[x, 0] = tile_types.wall
            dungeon.tiles[x, dungeon.height - 1] = tile_types.wall
        for y in range(dungeon.height):
            dungeon.tiles[0, y] = tile_types.wall
            dungeon.tiles[dungeon.width - 1, y] = tile_types.wall

        # 4. Place Player (find a safe spot in cavern)
        start_x, start_y = list(largest_cavern)[0]  # Just pick first valid point
        player.place(start_x, start_y, dungeon)

        # 5. Place Stairs (far from player)
        # Simple heuristic: random spot in cavern far from player
        self._place_downstairs(dungeon, largest_cavern, (start_x, start_y))

        # 6. Spawn Entities
        # We don't have "rooms" so we pick random spots in the cavern
        self._spawn_in_cavern(dungeon, largest_cavern, engine.game_world.current_floor)

        # Log map
        self._log_map(dungeon, engine.game_world.current_floor)

        return dungeon

    def _smooth_map(self, dungeon: GameMap) -> None:
        new_tiles = copy.deepcopy(dungeon.tiles)

        for y in range(1, dungeon.height - 1):
            for x in range(1, dungeon.width - 1):
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        if dungeon.tiles[x + dx, y + dy] == tile_types.wall:
                            neighbors += 1

                # Rule: 5-8 neighbors -> Wall, <5 -> Floor (simple smoothing)
                # Or standard 4-5 rule
                if neighbors > 4:
                    new_tiles[x, y] = tile_types.wall
                elif neighbors < 4:
                    new_tiles[x, y] = tile_types.floor

        dungeon.tiles = new_tiles

    def _get_largest_cavern(self, dungeon: GameMap) -> set[Tuple[int, int]]:
        visited = set()
        largest_cavern = set()

        for y in range(1, dungeon.height - 1):
            for x in range(1, dungeon.width - 1):
                if dungeon.tiles[x, y] == tile_types.floor and (x, y) not in visited:
                    # Flood fill
                    cavern = set()
                    stack = [(x, y)]
                    visited.add((x, y))

                    while stack:
                        cx, cy = stack.pop()
                        cavern.add((cx, cy))

                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if abs(dx) + abs(dy) != 1:
                                    continue  # Cardinal only
                                nx, ny = cx + dx, cy + dy
                                if (
                                    0 <= nx < dungeon.width
                                    and 0 <= ny < dungeon.height
                                    and dungeon.tiles[nx, ny] == tile_types.floor
                                    and (nx, ny) not in visited
                                ):
                                    visited.add((nx, ny))
                                    stack.append((nx, ny))

                    if len(cavern) > len(largest_cavern):
                        largest_cavern = cavern

        return largest_cavern

    def _place_downstairs(
        self,
        dungeon: GameMap,
        cavern: set[Tuple[int, int]],
        player_pos: Tuple[int, int],
    ) -> None:
        # Find farthest point simply
        farthest_dist = 0
        farthest_point = player_pos

        candidates = random.sample(list(cavern), min(50, len(cavern)))

        for x, y in candidates:
            dist = abs(x - player_pos[0]) + abs(y - player_pos[1])
            if dist > farthest_dist:
                farthest_dist = dist
                farthest_point = (x, y)

        sx, sy = farthest_point
        dungeon.tiles[sx, sy] = tile_types.down_stairs
        dungeon.downstairs_location = (sx, sy)

    def _spawn_in_cavern(
        self, dungeon: GameMap, cavern: set[Tuple[int, int]], floor: int
    ) -> None:
        # HACK: Create a fake "room" covering whole map for existing Spawner API,
        # OR just call spawner logic manually.
        # Since RandomTableSpawner expects a "room", we can't easily use it nicely without modification.
        # But for now, let's just create a dummy huge room that encompasses the map bounds
        # and let the spawner TRY to spawn.
        # Wait, standard spawner checks for collisions.

        # Better: use spawner but pass a bounding box of the whole map
        # Spawner picks random points in box. If point is WALL, spawn fails (or we retry).
        # Our spawner as written: "x = random.randint(room.x1 + 1, room.x2 - 1)"
        # It blindly spawns. We need to check walkability.

        pass  # Only implementing class structure for now to satisfy task.
        # Actually I should implement a valid spawn.

        # Simple manual spawn for now
        num_monsters = random.randint(0, 5)  # simplified
        num_items = random.randint(0, 3)

        # We need access to factories
        from src.entities import entity_factories
        import copy

        candidates = list(cavern)
        random.shuffle(candidates)

        # Spawn logic (simplified)
        for _ in range(num_monsters):
            if not candidates:
                break
            x, y = candidates.pop()
            if random.random() < 0.8:
                mon = copy.deepcopy(entity_factories.ghost)
            else:
                mon = copy.deepcopy(entity_factories.red_ghost)
            mon.spawn(dungeon, x, y)

        for _ in range(num_items):
            if not candidates:
                break
            x, y = candidates.pop()
            item = copy.deepcopy(entity_factories.health_potion)
            item.spawn(dungeon, x, y)

    def _log_map(self, dungeon: GameMap, floor: int) -> None:
        try:
            map_logger = get_map_logger()
            map_logger.log_map(dungeon, "cave", floor)
        except Exception as e:
            print(f"Warning: Failed to log map: {e}")
