from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .state import ThreadSafeGameState
from .routes.core import create_router as core_router
from .routes.media import create_router as media_router
from .routes.gameplay import create_router as gameplay_router


def create_app(game_state: ThreadSafeGameState, cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(
        title="Roguelike Game API",
        description="API for the roguelike game with pygame rendering",
        version="1.0.0",
    )

    # CORS for cross-machine access
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=600,
    )

    # Mount routers
    app.include_router(core_router(game_state))
    app.include_router(media_router(game_state))
    app.include_router(gameplay_router(game_state))

    return app


__all__ = ["create_app"]
