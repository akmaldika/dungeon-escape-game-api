from __future__ import annotations

from typing import cast

from src.app import setup_game
from src.core.engine import Engine as CoreEngine

class GameFactory:
    """Factory for creating game instances based on configuration strings."""

    @staticmethod
    def create_game_from_mode(mode_string: str) -> CoreEngine:
        """
        Create a game engine instance based on the mode string.
        
        Args:
            mode_string: The mode string (e.g., "custom|partial,8", "procedural|...", "string|...").
            
        Returns:
            A configured CoreEngine instance.
        """
        engine: CoreEngine
        
        if mode_string.startswith("custom|"):
            # Parse custom mode with FOV: "custom|partial,8"
            fov_parts = mode_string[7:].split(",") if "|" in mode_string else ["partial", "8"]
            fov_mode = fov_parts[0] if len(fov_parts) > 0 else "partial"
            fov_radius = int(fov_parts[1]) if len(fov_parts) > 1 else 8
            test_map = "custom_map.txt"
            engine = cast(CoreEngine, setup_game.new_game(
                use_custom_map=True, custom_map_file=test_map,
                fov_mode=fov_mode, fov_radius=fov_radius
            ))
        elif mode_string == "custom":
            # Fallback for old format
            test_map = "custom_map.txt"
            engine = cast(CoreEngine, setup_game.new_game(use_custom_map=True, custom_map_file=test_map))
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
            engine = cast(CoreEngine, setup_game.new_game(
                custom_map_string=custom_map_string,
                fov_mode=fov_mode, fov_radius=fov_radius
            ))
        elif mode_string.startswith("procedural|"):
            # Parse procedural parameters: "procedural|30,4,6,30,30,partial,8"
            param_string = mode_string[11:]  # Remove "procedural|"
            try:
                parts = param_string.split(",")
                max_rooms, room_min_size, room_max_size, map_width, map_height = map(int, parts[:5])
                fov_mode = parts[5] if len(parts) > 5 else "partial"
                fov_radius = int(parts[6]) if len(parts) > 6 else 8
                engine = cast(CoreEngine, setup_game.new_game(
                    use_custom_map=False,
                    max_rooms=max_rooms,
                    room_min_size=room_min_size,
                    room_max_size=room_max_size,
                    map_width=map_width,
                    map_height=map_height,
                    fov_mode=fov_mode,
                    fov_radius=fov_radius
                ))
            except (ValueError, TypeError):
                # Fallback to defaults if parsing fails
                engine = cast(CoreEngine, setup_game.new_game(use_custom_map=False))
        else:
            engine = cast(CoreEngine, setup_game.new_game(use_custom_map=False))
            
        return engine
