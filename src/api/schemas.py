from typing import Any, Literal
from pydantic import BaseModel


class StartGameRequest(BaseModel):
    mode: Literal["procedural", "custom", "string"] = "procedural"
    custom_map: str | None = None  # String representation of the map
    # Procedural generation parameters (only used if mode="procedural")
    max_rooms: int | None = 30
    room_min_size: int | None = 4
    room_max_size: int | None = 6
    map_width: int | None = 30
    map_height: int | None = 30
    # FOV configuration
    fov_mode: Literal["partial", "all"] = "partial"
    fov_radius: int = 8  # Only used if fov_mode="partial"


class PerformActionRequest(BaseModel):
    action: str


class GameStateResponse(BaseModel):
    dungeon_level: int
    current_level_step_count: int
    message_log: list[str]
    player_standing_on: str
    player_health: int
    health_potion_count: int
    player_position: list[int]  # [x, y] coordinates
    stairs: tuple[int, int] | None = None
    is_done: bool
    end_reason: str | None = None
    legal_actions: list[str]


class PerformActionResponse(BaseModel):
    action_executed: str
    state_changes: GameStateResponse



