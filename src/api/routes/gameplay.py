from __future__ import annotations

import time
from fastapi import APIRouter, HTTPException

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
            game_state.queue_action(f"restart_string|{request.custom_map}")
        else:
            game_state.queue_action(f"restart_{request.mode}")

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
    async def perform_action(request: PerformActionRequest):
        valid_actions = ['w', 'a', 's', 'd', 'up', 'down', 'left', 'right', 'space', 'g', 'i', '.']
        if request.action.lower() not in valid_actions:
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

        # Queue the action for the main game loop
        game_state.queue_action(request.action.lower())

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

    @router.post("/action", response_model=PerformActionResponse)  # type: ignore[misc]
    async def action_alias(request: PerformActionRequest):
        return await perform_action(request)

    return router


__all__ = ["create_router"]
