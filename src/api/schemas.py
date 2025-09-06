from typing import Optional, Dict, List, Any, Tuple
from pydantic import BaseModel


class StartGameRequest(BaseModel):
    mode: str = "procedural"
    custom_map: Optional[str] = None  # String representation of the map


class PerformActionRequest(BaseModel):
    action: str


class GameStateResponse(BaseModel):
    dungeon_level: int
    current_level_step_count: int
    message_log: List[str]
    player_standing_on: str
    player_health: int
    health_potion_count: int
    is_done: bool
    end_reason: Optional[str] = None
    legal_actions: List[str]


class PerformActionResponse(BaseModel):
    action_executed: str
    state_changes: "GameStateResponse"


class ObservationResponse(BaseModel):
    step_id: int
    dungeon_level: int
    is_done: bool
    end_reason: Optional[str] = None
    screenshot_png_base64: str
    player: Dict[str, Any]
    enemies: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    stairs: Optional[Tuple[int, int]]
    visible_mask: List[List[bool]]
    legal_actions: List[str]
    message_log: List[str]
