from typing import Tuple

import numpy as np  # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
	[
		("ch", np.int32),  # Unicode codepoint.
		("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
		("bg", "3B"),
	]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
	[
		("walkable", bool),  # True if this tile can be walked over.
		("transparent", bool),  # True if this tile doesn't block FOV.
		("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
		("light", graphic_dt),  # Graphics for when the tile is in FOV.
	]
)


def new_tile(
	*,  # Enforce the use of keywords, so that parameter order doesn't matter.
	walkable: int,
	transparent: int,
	dark: Tuple[int, Tuple[int, int, int], Tuple],
	light: Tuple[int, Tuple[int, int, int], Tuple],
) -> np.ndarray:
	"""Helper function for defining individual tile types """
	return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Use the custom tile graphics for floor and wall
floor = new_tile(
	walkable=True,
	transparent=True,
	# Use the dark floor graphic (0x100004) when not in FOV
	dark=(0x100004, (255, 255, 255), (0, 0, 0)), 
	# Use the light floor graphic (0x100003) when in FOV
	light=(0x100003, (255, 255, 255), (0, 0, 0)),
)
wall = new_tile(
	walkable=False,
	transparent=False,
	# Use the dark wall graphic (0x100006) when not in FOV
	dark=(0x100006, (255, 255, 255), (0, 0, 0)),
	# Use the light wall graphic (0x100005) when in FOV
	light=(0x100005, (255, 255, 255), (0, 0, 0)),
)
down_stairs = new_tile(
	walkable=True,
	transparent=True,
	dark=(0x100007, (0, 0, 100), (50, 50, 150)),
	# dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
	light=(0x100007, (255, 255, 255), (200, 180, 50)),
	# light=(ord(">"), (255, 255, 255), (200, 180, 50)),
)

