from dataclasses import dataclass


@dataclass
class MapConfiguration:
    """Configuration for map generation."""

    map_width: int
    map_height: int
    max_rooms: int
    room_min_size: int
    room_max_size: int

    # Defaults (can be overridden)
    fov_radius: int = 8
