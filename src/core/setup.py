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


def new_game(use_custom_map=False, custom_map_file="", custom_map_string="", 
             max_rooms=30, room_min_size=4, room_max_size=6, map_width=80, map_height=40,
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


def create_game_from_mode(mode_string: str) -> Engine:
    """
    Create a game engine instance based on the mode string.
    
    Args:
        mode_string: The mode string (e.g., "custom|partial,8", "procedural|...", "string|...").
        
    Returns:
        A configured Engine instance.
    """
    engine: Engine
    
    if mode_string.startswith("custom|"):
        # Parse custom mode with FOV: "custom|partial,8"
        fov_parts = mode_string[7:].split(",") if "|" in mode_string else ["partial", "8"]
        fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
        fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
        test_map = "custom_map.txt"
        engine = new_game(
            use_custom_map=True, custom_map_file=test_map,
            fov_mode=fov_mode, fov_radius=fov_radius
        )
    elif mode_string == "custom":
        # Fallback for old format
        test_map = "custom_map.txt"
        engine = new_game(use_custom_map=True, custom_map_file=test_map)
    elif mode_string.startswith("string|"):
        # Parse string mode: "string|map_data|partial,8"
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
            fov_mode=fov_mode, fov_radius=fov_radius
        )
    elif mode_string.startswith("procedural|"):
        # Parse procedural parameters: "procedural|max_rooms,min_size,max_size,width,height,fov_mode,fov_radius"
        # Example: "procedural|30,4,6,30,20,partial,8" -> Generates a 30x20 map
        param_string = mode_string[11:]  # Remove "procedural|"
        try:
            parts = param_string.split(",")
            # Defaults
            max_rooms = 30
            room_min_size = 4
            room_max_size = 6
            map_width = 80 # Default to full map size
            map_height = 40 # Default to full map size
            fov_mode = "partial"
            fov_radius = 8
            
            if len(parts) >= 1: max_rooms = int(parts[0])
            if len(parts) >= 2: room_min_size = int(parts[1])
            if len(parts) >= 3: room_max_size = int(parts[2])
            if len(parts) >= 4: map_width = int(parts[3])
            if len(parts) >= 5: map_height = int(parts[4])
            if len(parts) >= 6: fov_mode = parts[5]
            if len(parts) >= 7: fov_radius = int(parts[6])

            engine = new_game(
                use_custom_map=False,
                max_rooms=max_rooms,
                room_min_size=room_min_size,
                room_max_size=room_max_size,
                map_width=map_width,
                map_height=map_height,
                fov_mode=fov_mode,
                fov_radius=fov_radius
            )
        except (ValueError, TypeError):
            # Fallback to defaults if parsing fails
            engine = new_game(use_custom_map=False)
    else:
        engine = new_game(use_custom_map=False)
        
    return engine
