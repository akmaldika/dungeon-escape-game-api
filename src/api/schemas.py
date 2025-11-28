from typing import Optional, Dict, List, Any, Tuple
from pydantic import BaseModel


class StartGameRequest(BaseModel):
    mode: str = "procedural"
    custom_map: Optional[str] = None  # String representation of the map
    # Procedural generation parameters (only used if mode="procedural")
    max_rooms: Optional[int] = 30
    room_min_size: Optional[int] = 4
    room_max_size: Optional[int] = 6
    map_width: Optional[int] = 30
    map_height: Optional[int] = 30
    # FOV configuration
    fov_mode: str = "partial"  # "partial" or "all"
    fov_radius: int = 8  # Only used if fov_mode="partial"


class PerformActionRequest(BaseModel):
    action: str


class GameStateResponse(BaseModel):
    dungeon_level: int
    current_level_step_count: int
    message_log: List[str]
    player_standing_on: str
    player_health: int
    health_potion_count: int
    player_position: List[int]  # [x, y] coordinates
    stairs: Optional[Tuple[int, int]] = None
    is_done: bool
    end_reason: Optional[str] = None
    legal_actions: List[str]


class PerformActionResponse(BaseModel):
    action_executed: str
    state_changes: "GameStateResponse"



