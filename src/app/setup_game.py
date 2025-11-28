"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
from typing import Optional

import tcod
from tcod import libtcodpy

from PIL import Image
import numpy as np

from src.core import color
from src.core.engine import Engine
from src.core import entity_factories
from src.core.game_map import GameWorld
from src.core import input_handlers
from src.core.custom_map_loader import load_custom_map, load_custom_map_from_string
from src.core.map_logger import get_map_logger


# Load the background image with Pillow and ensure it's RGB (no alpha channel).
bg_img = Image.open("assets/menu_background.png").convert("RGB")
background_image = np.asarray(bg_img, dtype=np.uint8)


def new_game(use_custom_map=False, custom_map_file="", custom_map_string="", 
             max_rooms=30, room_min_size=4, room_max_size=6, map_width=30, map_height=30,
             fov_mode="partial", fov_radius=8) -> Engine:
	"""Return a brand new game session as an Engine instance."""

	player = copy.deepcopy(entity_factories.player)

	engine = Engine(player=player, fov_mode=fov_mode, fov_radius=fov_radius)
	engine.is_using_custom_map = use_custom_map or bool(custom_map_string)  # Set the flag

	if custom_map_string:
		# Load from string
		engine.game_world = GameWorld(
			engine=engine,
			max_rooms=max_rooms,
			room_min_size=room_min_size,
			room_max_size=room_max_size,
			map_width=map_width,
			map_height=map_height,
		)
		engine.game_world.current_floor = 1  # Set to 1 for custom maps
		engine.game_map = load_custom_map_from_string(custom_map_string, engine)
		
		# Log string map
		try:
			map_logger = get_map_logger()
			map_logger.log_map(engine.game_map, "string", 1)
		except Exception as e:
			print(f"Warning: Failed to log string map: {e}")
			
	elif use_custom_map:
		# Load from file
		engine.game_world = GameWorld(
			engine=engine,
			max_rooms=max_rooms,
			room_min_size=room_min_size,
			room_max_size=room_max_size,
			map_width=map_width,
			map_height=map_height,
		)
		engine.game_world.current_floor = 1  # Set to 1 for custom maps
		engine.game_map = load_custom_map(custom_map_file, engine)
		
		# Log custom map
		try:
			map_logger = get_map_logger()
			map_logger.log_map(engine.game_map, "custom", 1)
		except Exception as e:
			print(f"Warning: Failed to log custom map: {e}")
			
	else:
		# Generate procedurally
		engine.game_world = GameWorld(
			engine=engine,
			max_rooms=max_rooms,
			room_min_size=room_min_size,
			room_max_size=room_max_size,
			map_width=map_width,
			map_height=map_height,
		)
		engine.game_world.generate_floor()
    
	engine.update_fov()

	engine.message_log.add_message(
		"Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
	)

    
	potions = [copy.deepcopy(entity_factories.health_potion) for _ in range(2)]

	for potion in potions:
		potion.parent = player.inventory

	for potion in potions:
		player.inventory.items.append(potion)

	return engine


class MainMenu(input_handlers.BaseEventHandler):
	"""Handle the main menu rendering and input."""

	def on_render(self, console: tcod.console.Console) -> None:
		"""Render the main menu on a background image."""
		console.draw_semigraphics(background_image, 0, 0)

		console.print(
			console.width // 2,
			console.height // 2 - 4,
			"TOMBS OF ANCIENT AI AGENT",
			fg=color.menu_title,
			alignment=libtcodpy.CENTER,
		)
		console.print(
			console.width // 2,
			console.height - 2,
			"By Akmal Mahardika Nurwahyu Pratama",
			fg=color.menu_title,
			alignment=libtcodpy.CENTER,
		)

		menu_width = 30
		for i, text in enumerate([
			"[N] Play a new game",
			"[S] Static map test",
			"[Q] Quit",
		]):
			console.print(
				console.width // 2,
				console.height // 2 - 2 + i,
				text.ljust(menu_width),
				fg=color.menu_text,
				bg=color.black,
				alignment=libtcodpy.CENTER,
				bg_blend=libtcodpy.BKGND_ALPHA(64),
			)

	def ev_keydown(
		self, event: tcod.event.KeyDown
	) -> Optional[input_handlers.BaseEventHandler]:
		if event.sym in (tcod.event.KeySym.Q, tcod.event.KeySym.ESCAPE):
			raise SystemExit()
		elif event.sym == tcod.event.KeySym.N:
			return input_handlers.MainGameEventHandler(new_game(use_custom_map=False))
		elif event.sym == tcod.event.KeySym.S:
			# Test static map - menggunakan salah satu map dari data/map/new/
			test_map = "custom_map.txt"
			return input_handlers.MainGameEventHandler(new_game(use_custom_map=True, custom_map_file=test_map))

		return None

