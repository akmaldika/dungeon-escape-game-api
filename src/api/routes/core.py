from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, HTTPException

from ..schemas import (
    StartGameRequest,
    PerformActionRequest,
    GameStateResponse,
    PerformActionResponse,
    ObservationResponse,
)
from ..state import ThreadSafeGameState
from ..observation import build_observation_payload


def create_router(game_state: ThreadSafeGameState) -> APIRouter:
    router = APIRouter()

    @router.get("/", tags=["meta"])  # type: ignore[misc]
    async def root():
        return {
            "message": "Roguelike Game API - Pygame Renderer",
            "status": "running" if game_state.engine else "waiting_for_game",
            "renderer": "pygame",
            "tile_size": game_state.renderer.tile_size if game_state.renderer else "unknown",
        }

    @router.get("/game-state", response_model=GameStateResponse, tags=["state"])  # type: ignore[misc]
    async def get_game_state():
        state = game_state.get_state_snapshot()
        if not state:
            raise HTTPException(status_code=400, detail="No active game session")
        return state

    @router.get("/observation", response_model=ObservationResponse, tags=["state"])  # type: ignore[misc]
    async def observation():
        return build_observation_payload(game_state)

    return router


__all__ = ["create_router"]
