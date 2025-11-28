"""
Custom Map Loader - Load game maps from string or file.

Character Mapping:
    # = wall (blocked, tidak bisa dilewati)
    . = floor (walkable, bisa dilewati)
    (space) = void (black space, luar map)
    @ = Player (starting position)
    > = Stairs (down stairs ke floor berikutnya)
    O = Ghost (musuh basic)
    T = Red Ghost / Troll (musuh kuat)
    h = Health Potion (item consumable)
"""
import copy
from src.core import tile_types
from src.core import entity_factories
from src.core.game_map import GameMap


def load_custom_map_from_string(map_string, engine):
	"""
	Load a map from a string representation.
	
	Args:
		map_string: String representation of the map
		engine: Game engine instance
	
	Returns:
		GameMap: Loaded game map
	"""
	lines = map_string.split('\n')
    
	height = len(lines)
	width = max(len(line) for line in lines)
	game_map = GameMap(engine, width, height, entities=[])

	# Initialize all tiles as void (black space)
	game_map.tiles[:] = tile_types.void

	for y, line in enumerate(lines):
		for x in range(width):
			char = line[x] if x < len(line) else ' '
			
			if char == "#":
				# Wall - blocked tile
				game_map.tiles[x, y] = tile_types.wall
			elif char == ".":
				# Floor - walkable tile
				game_map.tiles[x, y] = tile_types.floor
			elif char == "@":
				# Player starting position
				game_map.tiles[x, y] = tile_types.floor
				engine.player.place(x, y, game_map)
				game_map.entities.add(engine.player)
			elif char == ">":
				# Stairs down
				game_map.tiles[x, y] = tile_types.down_stairs
				game_map.downstairs_location = (x, y)
			elif char == "O":
				# Ghost enemy
				game_map.tiles[x, y] = tile_types.floor
				ghost = copy.deepcopy(entity_factories.ghost)
				ghost.place(x, y, game_map)
				game_map.entities.add(ghost)
			elif char == "T":
				# Red Ghost / Troll enemy
				game_map.tiles[x, y] = tile_types.floor
				red_ghost = copy.deepcopy(entity_factories.troll)
				red_ghost.place(x, y, game_map)
				game_map.entities.add(red_ghost)
			elif char == "h":
				# Health Potion item
				game_map.tiles[x, y] = tile_types.floor
				health_potion = copy.deepcopy(entity_factories.health_potion)
				health_potion.place(x, y, game_map)
				game_map.entities.add(health_potion)
			elif char == " ":
				# Void / black space (default)
				game_map.tiles[x, y] = tile_types.void

	return game_map


def load_custom_map(filename, engine):
	"""
	Load a map from a file.
	
	Args:
		filename: Path to the map file
		engine: Game engine instance
	
	Returns:
		GameMap: Loaded game map
	"""
	with open(filename, "r") as f:
		map_string = f.read()
	
	return load_custom_map_from_string(map_string, engine)

