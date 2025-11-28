from __future__ import annotations

import time
from fastapi import APIRouter, HTTPException, Request
import logging
from logging.handlers import RotatingFileHandler
import os

# Module logger for gameplay endpoints
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Ensure we have a handler that writes to a file for /perform-action audit
    os.makedirs("log", exist_ok=True)
    fh = RotatingFileHandler(os.path.join("log", "api_actions.log"), maxBytes=5 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
logger.setLevel(logging.INFO)

from ..schemas import (
    StartGameRequest,
    PerformActionRequest,
    GameStateResponse,
    PerformActionResponse,
)
from ..state import ThreadSafeGameState


def create_router(game_state: ThreadSafeGameState) -> APIRouter:
    router = APIRouter()

    @router.post("/start-game", response_model=GameStateResponse)  # type: ignore[misc]
    async def start_game(request: StartGameRequest):
        if request.mode not in ["custom", "procedural", "string"]:
            raise HTTPException(status_code=400, detail="Mode must be 'custom', 'procedural', or 'string'")

        if request.mode == "string" and not request.custom_map:
            raise HTTPException(status_code=400, detail="custom_map is required when mode is 'string'")

        # Queue a restart action - this will be handled by the main game loop
        if request.mode == "string":
            # Include FOV parameters for string mode
            fov_params = f"{request.fov_mode},{request.fov_radius}"
            game_state.queue_action(f"restart_string|{request.custom_map}|{fov_params}")
        elif request.mode == "procedural":
            # Include procedural and FOV parameters
            params = f"{request.max_rooms},{request.room_min_size},{request.room_max_size},{request.map_width},{request.map_height},{request.fov_mode},{request.fov_radius}"
            game_state.queue_action(f"restart_procedural|{params}")
        else:
            # Include FOV parameters for custom mode
            fov_params = f"{request.fov_mode},{request.fov_radius}"
            game_state.queue_action(f"restart_{request.mode}|{fov_params}")

        # Wait deterministically for the game to restart
        deadline = time.monotonic() + 0.5
        state = None
        while time.monotonic() < deadline:
            state = game_state.get_state_snapshot()
            if state:
                break
            time.sleep(0.01)
        if not state:
            raise HTTPException(status_code=500, detail="Failed to start game")
        return state

    @router.post("/perform-action", response_model=PerformActionResponse)  # type: ignore[misc]
    async def perform_action(request: PerformActionRequest, http_request: Request):
        valid_actions = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right', 'space', 'g', 'i', '.', 'esc', 'q']
        if request.action.lower() not in valid_actions:
            # Log invalid attempts
            try:
                client_host = http_request.client.host if http_request.client else "unknown"
            except Exception:
                client_host = "unknown"
            logger.warning(
                "perform-action invalid: action=%s; client=%s; ua=%s",
                request.action,
                client_host,
                http_request.headers.get("user-agent", ""),
            )
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

        # Audit-log the incoming perform-action request
        try:
            client_host = http_request.client.host if http_request.client else "unknown"
        except Exception:
            client_host = "unknown"

        ua = http_request.headers.get("user-agent", "")
        logger.info(
            "perform-action received: action=%s; client=%s; ua=%s",
            request.action,
            client_host,
            ua,
        )

        # Queue the action for the main game loop
        action_lower = request.action.lower()
        game_state.queue_action(action_lower)
        logger.info("perform-action queued: action=%s; client=%s", action_lower, client_host)

        # Wait deterministically for step advancement or dungeon change
        prev = None
        first = game_state.get_state_snapshot()
        if first:
            prev = (first.get("current_level_step_count"), first.get("dungeon_level"))
        deadline = time.monotonic() + 0.5
        state = first
        while time.monotonic() < deadline:
            state = game_state.get_state_snapshot()
            if not state:
                break
            if prev is None:
                break
            if (state.get("current_level_step_count"), state.get("dungeon_level")) != prev:
                break
            time.sleep(0.01)
        if not state:
            raise HTTPException(status_code=400, detail="No active game session")

        return {
            "action_executed": request.action,
            "state_changes": state,
        }



    return router


__all__ = ["create_router"]
