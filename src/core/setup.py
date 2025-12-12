"""
Game Setup and Factory.

Handles the initialization of game sessions and creation of game engines from various configurations.
"""

from __future__ import annotations

import copy
from typing import cast

from src.core import color
from src.core.engine import Engine
from src.entities import entity_factories
from src.map.game_map import GameWorld
from src.map.custom_map_loader import load_custom_map, load_custom_map_from_string
from src.map.map_logger import get_map_logger


def new_game(
    use_custom_map=False,
    custom_map_file="",
    custom_map_string="",
    max_rooms=30,
    room_min_size=4,
    room_max_size=6,
    map_width=80,
    map_height=40,
    fov_mode="partial",
    fov_radius=8,
    map_gen_type="dungeon",
) -> Engine:
    """Return a brand new game session as an Engine instance."""

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player, fov_mode=fov_mode, fov_radius=fov_radius)
    engine.is_using_custom_map = use_custom_map or bool(
        custom_map_string
    )  # Set the flag

    if custom_map_string:
        # Load from string
        engine.game_world = GameWorld(
            engine=engine,
            max_rooms=max_rooms,
            room_min_size=room_min_size,
            room_max_size=room_max_size,
            map_width=map_width,
            map_height=map_height,
            map_gen_type=map_gen_type,
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
            map_gen_type=map_gen_type,
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
            map_gen_type=map_gen_type,
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


def create_game_from_mode(mode_string: str) -> Engine:
    """
    Create a game engine instance based on the mode string.

    Args:
        mode_string: The mode string.

    Returns:
        A configured Engine instance.
    """
    engine: Engine

    if mode_string.startswith("custom|"):
        # Parse custom mode with FOV: "custom|partial,8"
        fov_parts = (
            mode_string[7:].split(",") if "|" in mode_string else ["partial", "8"]
        )
        fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
        fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
        test_map = "custom_map.txt"
        engine = new_game(
            use_custom_map=True,
            custom_map_file=test_map,
            fov_mode=fov_mode,
            fov_radius=fov_radius,
        )
    elif mode_string == "custom":
        test_map = "custom_map.txt"
        engine = new_game(use_custom_map=True, custom_map_file=test_map)

    elif mode_string.startswith("string|"):
        parts = mode_string[7:].split("|")
        custom_map_string = parts[0]
        if len(parts) > 1:
            fov_parts = parts[1].split(",")
            fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
            fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
        else:
            fov_mode, fov_radius = "partial", 8
        engine = new_game(
            custom_map_string=custom_map_string,
            fov_mode=fov_mode,
            fov_radius=fov_radius,
        )

    elif mode_string.startswith("procedural|") or mode_string.startswith("cellular|"):
        # "procedural|..." or "cellular|..."
        is_cellular = mode_string.startswith("cellular|")
        prefix_len = 9 if is_cellular else 11
        map_gen_type = "cellular" if is_cellular else "dungeon"

        param_string = mode_string[prefix_len:]

        try:
            parts = param_string.split(",")
            # Defaults
            max_rooms = 30
            room_min_size = 4
            room_max_size = 6
            map_width = 80
            map_height = 40
            fov_mode = "partial"
            fov_radius = 8

            if len(parts) >= 1 and parts[0]:
                max_rooms = int(parts[0])
            if len(parts) >= 2 and parts[1]:
                room_min_size = int(parts[1])
            if len(parts) >= 3 and parts[2]:
                room_max_size = int(parts[2])
            if len(parts) >= 4 and parts[3]:
                map_width = int(parts[3])
            if len(parts) >= 5 and parts[4]:
                map_height = int(parts[4])
            if len(parts) >= 6 and parts[5]:
                fov_mode = parts[5]
            if len(parts) >= 7 and parts[6]:
                fov_radius = int(parts[6])

            engine = new_game(
                use_custom_map=False,
                max_rooms=max_rooms,
                room_min_size=room_min_size,
                room_max_size=room_max_size,
                map_width=map_width,
                map_height=map_height,
                fov_mode=fov_mode,
                fov_radius=fov_radius,
                map_gen_type=map_gen_type,
            )
        except (ValueError, TypeError):
            engine = new_game(use_custom_map=False, map_gen_type=map_gen_type)

    else:
        # Default fallback
        engine = new_game(use_custom_map=False)

    return engine
