import copy
import tile_types
import entity_factories
from game_map import GameMap

def load_custom_map_from_string(map_string, engine):
    """Load a map from a string representation."""
    lines = map_string.split('\n')
    
    height = len(lines)
    width = max(len(line) for line in lines)
    game_map = GameMap(engine, width, height, entities=[])

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "#":
                game_map.tiles[x, y] = tile_types.wall
            elif char == ".":
                game_map.tiles[x, y] = tile_types.floor
            elif char == "@":
                game_map.tiles[x, y] = tile_types.floor
                engine.player.place(x, y, game_map)
                game_map.entities.add(engine.player)
            elif char == ">":
                game_map.tiles[x, y] = tile_types.down_stairs
                game_map.downstairs_location = (x, y)
            elif char == "O":
                # Monster type 2 (enemy weak) - Ghost
                game_map.tiles[x, y] = tile_types.floor
                ghost = copy.deepcopy(entity_factories.ghost)
                ghost.place(x, y, game_map)
                game_map.entities.add(ghost)
            elif char == "T":
                # Monster type 1 (enemy strong) - Red Ghost
                game_map.tiles[x, y] = tile_types.floor
                troll = copy.deepcopy(entity_factories.troll)
                troll.place(x, y, game_map)
                game_map.entities.add(troll)
            elif char == "h":
                # Health potion
                game_map.tiles[x, y] = tile_types.floor
                health_potion = copy.deepcopy(entity_factories.health_potion)
                health_potion.place(x, y, game_map)
                game_map.entities.add(health_potion)

    return game_map

def load_custom_map(filename, engine):
    with open(filename, "r") as f:
        lines = [line.rstrip("\n") for line in f]

    height = len(lines)
    width = max(len(line) for line in lines)
    game_map = GameMap(engine, width, height, entities=[])

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "#":
                game_map.tiles[x, y] = tile_types.wall
            elif char == ".":
                game_map.tiles[x, y] = tile_types.floor
            elif char == "@":
                game_map.tiles[x, y] = tile_types.floor
                engine.player.place(x, y, game_map)
                game_map.entities.add(engine.player)
            elif char == ">":
                game_map.tiles[x, y] = tile_types.down_stairs
                game_map.downstairs_location = (x, y)
            elif char == "O":
                # Monster type 2 (enemy weak) - Ghost
                game_map.tiles[x, y] = tile_types.floor
                ghost = copy.deepcopy(entity_factories.ghost)
                ghost.place(x, y, game_map)
                game_map.entities.add(ghost)
            elif char == "T":
                # Monster type 1 (enemy strong) - Red/Ghost
                game_map.tiles[x, y] = tile_types.floor
                troll = copy.deepcopy(entity_factories.troll)
                troll.place(x, y, game_map)
                game_map.entities.add(troll)
            elif char == "h":
                # Health potion
                game_map.tiles[x, y] = tile_types.floor
                health_potion = copy.deepcopy(entity_factories.health_potion)
                health_potion.place(x, y, game_map)
                game_map.entities.add(health_potion)

    return game_map