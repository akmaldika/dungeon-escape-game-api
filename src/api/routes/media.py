from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
import io

from PIL import Image  # type: ignore
import pygame  # type: ignore

from ..state import ThreadSafeGameState


def create_router(game_state: ThreadSafeGameState) -> APIRouter:
    router = APIRouter()

    @router.get("/game-screenshot")  # type: ignore[misc]
    async def get_game_screenshot(fmt: str = "b64"):
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

        if fmt.lower() == "bytes":
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
        else:
            # Base64 JSON payload for consistency with /observation
            import base64
            b64 = base64.b64encode(screenshot_data).decode('ascii')
            return {
                "screenshot_png_base64": b64,
                "tile_size": tile_size,
                "total_width_tiles": total_width_tiles,
                "total_height_tiles": total_height_tiles,
                "map_width_tiles": map_width_tiles,
                "map_height_tiles": map_height_tiles,
                "total_width_pixels": total_width_tiles * tile_size,
                "total_height_pixels": total_height_tiles * tile_size,
                "map_width_pixels": map_width_tiles * tile_size,
                "map_height_pixels": map_height_tiles * tile_size,
            }

    @router.get("/sprite/{name}.png")  # type: ignore[misc]
    async def get_sprite(name: str):
        renderer = game_state.renderer
        if not renderer:
            raise HTTPException(status_code=400, detail="Renderer not initialized")

        key = name.lower().replace('.png', '')
        alias = {"stairs": "ladder", "potion": "chest", "health_potion": "chest"}
        key = alias.get(key, key)

        surface = renderer.sprites.get(key)
        if surface is None:
            surface = pygame.Surface((renderer.tile_size, renderer.tile_size))
            surface.fill((128, 128, 128))

        raw = pygame.image.tostring(surface, 'RGB')
        img = Image.frombytes('RGB', (renderer.tile_size, renderer.tile_size), raw)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png", headers={"X-Tile-Size": str(renderer.tile_size)})

    return router


__all__ = ["create_router"]
