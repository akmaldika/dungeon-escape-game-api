from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
import io

from PIL import Image  # type: ignore
import pygame  # type: ignore

from ..state import ThreadSafeGameState


def create_router(game_state: ThreadSafeGameState) -> APIRouter:
    router = APIRouter()

    @router.get("/game-screenshot")  # type: ignore[misc]
    async def get_game_screenshot():
        screenshot_data = game_state.get_screenshot_data()
        if not screenshot_data:
            raise HTTPException(status_code=400, detail="No active game or failed to capture screenshot")

        # Calculate dimensions
        tile_size = game_state.renderer.tile_size if game_state.renderer else 16
        total_width_tiles = game_state.renderer.width if game_state.renderer else 80
        total_height_tiles = game_state.renderer.height if game_state.renderer else 40

        # Get actual map dimensions (excluding UI)
        map_width_tiles = 30  # Default fallback
        map_height_tiles = 30  # Default fallback

        if game_state.engine and game_state.engine.game_map:
            map_width_tiles = game_state.engine.game_map.width
            map_height_tiles = game_state.engine.game_map.height

        # Raw PNG bytes response
        return Response(
            content=screenshot_data,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=game_screenshot.png",
                "X-Tile-Size": str(tile_size),
                "X-Total-Width-Tiles": str(total_width_tiles),
                "X-Total-Height-Tiles": str(total_height_tiles),
                "X-Map-Width-Tiles": str(map_width_tiles),
                "X-Map-Height-Tiles": str(map_height_tiles),
                "X-Total-Width-Pixels": str(total_width_tiles * tile_size),
                "X-Total-Height-Pixels": str(total_height_tiles * tile_size),
                "X-Map-Width-Pixels": str(map_width_tiles * tile_size),
                "X-Map-Height-Pixels": str(map_height_tiles * tile_size),
            },
        )



    return router


__all__ = ["create_router"]
