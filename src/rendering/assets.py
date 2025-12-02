from __future__ import annotations

import os
import pygame
from typing import Dict, Tuple, Optional

from src.core.config import get_sprite_directory
from src.core import color

class AssetLoader:
    """Handles loading and management of game assets (sprites, fonts)."""
    
    def __init__(self, tile_size: int):
        self.tile_size = tile_size
        self.sprites: Dict[str, pygame.Surface] = {}
        self.font_small: pygame.font.Font | None = None
        self.font_large: pygame.font.Font | None = None
        self.font: pygame.font.Font | None = None
        
        # Initialize fonts
        if pygame.font.get_init():
            if tile_size <= 8:
                base_font_size = 8  # Larger relative size for readability
                title_font_size = 20
            else:
                base_font_size = 16
                title_font_size = 40
            
            font_family = "assets/fonts/PixelOperator8.ttf"
            self.font_small = pygame.font.Font(font_family, base_font_size)
            self.font_large = pygame.font.Font(font_family, title_font_size)
            self.font = self.font_small
            
        # Disable antialiasing for small tile sizes (pixel art look)
        self.antialias = self.tile_size >= 16
        
        self.load_assets()

    def load_assets(self) -> None:
        """Load assets based on the current rendering mode."""
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load sprites from files."""
        # Get sprite directory based on tile_size
        try:
            sprite_dir = get_sprite_directory(self.tile_size)
        except ValueError:
            print(f"Warning: Unsupported tile size {self.tile_size}, using default assets.")
            sprite_dir = "assets/8x8" # Fallback

        # Asset paths
        sprite_names = [
            'player', 'ghost', 'red_ghost', 'floor', 'dark_floor',
            'wall', 'dark_wall', 'ladder', 'wooden_box',
        ]
        
        for name in sprite_names:
            path = f'{sprite_dir}/{name}.png'
            if os.path.exists(path):
                try:
                    # Load and scale to exact tile size
                    image = pygame.image.load(path)
                    scaled_image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
                    self.sprites[name] = scaled_image
                except Exception as e:
                    print(f"Failed to load sprite {name}: {e}")
                    self.sprites[name] = self.create_colored_tile(color.error)
            else:
                self.sprites[name] = self.create_colored_tile(self._get_fallback_color(name))

    def _get_fallback_color(self, name: str) -> Tuple[int, int, int]:
        """Get fallback color for a missing sprite."""
        colors = {
            'player': color.player,
            'ghost': color.ghost,
            'red_ghost': color.red_ghost,
            'floor': color.floor,
            'dark_floor': color.floor,
            'wall': color.wall,
            'dark_wall': color.wall,
            'ladder': color.stairs,
            'wooden_box': color.health_potion,
        }
        return colors.get(name, color.error)

    def create_colored_tile(self, color: Tuple[int, int, int]) -> pygame.Surface:
        """Create a colored rectangle tile."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(color)
        return surface

    def create_text_tile(self, char: str, color: Tuple[int, int, int], bg_color: Tuple[int, int, int] = (0, 0, 0)) -> pygame.Surface:
        """Create a tile with a character."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(bg_color)
        
        if self.font:
            text_surface = self.font.render(char, self.antialias, color)
            # Center the text
            text_rect = text_surface.get_rect(center=(self.tile_size // 2, self.tile_size // 2))
            surface.blit(text_surface, text_rect)
        
        return surface

    def get_sprite(self, name: str) -> pygame.Surface:
        """Get a sprite by name, returning a default tile if not found."""
        return self.sprites.get(name, self.create_colored_tile(color.error))
