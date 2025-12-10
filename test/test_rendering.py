
import pytest
import pygame
from src.core.config import RenderingMode, CURRENT_RENDERING_MODE
import src.core.config
from src.rendering.assets import AssetLoader

def test_asset_loader_sprite_mode():
    """Test loading assets in SPRITE mode."""
    # Force SPRITE mode
    src.core.config.CURRENT_RENDERING_MODE = RenderingMode.SPRITE
    
    loader = AssetLoader(tile_size=8)
    assert 'player' in loader.sprites
    # In sprite mode, it loads from file. If file exists, it's a surface.
    assert isinstance(loader.sprites['player'], pygame.Surface)

def test_asset_loader_char_mode():
    """Test loading assets in CHAR mode."""
    # Force CHAR mode
    src.core.config.CURRENT_RENDERING_MODE = RenderingMode.CHAR
    
    loader = AssetLoader(tile_size=16)
    assert 'player' in loader.sprites
    assert isinstance(loader.sprites['player'], pygame.Surface)
    
    # Check that we have generated assets
    # We can't easy check pixel content without extensive setup, 
    # but we can check if it runs without error.

def test_asset_loader_char_color_mode():
    """Test loading assets in CHAR_COLOR mode."""
    # Force CHAR_COLOR mode
    src.core.config.CURRENT_RENDERING_MODE = RenderingMode.CHAR_COLOR
    
    loader = AssetLoader(tile_size=16)
    assert 'player' in loader.sprites
    assert isinstance(loader.sprites['player'], pygame.Surface)

def test_fallback_logic():
    """Test that missing sprites fallback correctly."""
    src.core.config.CURRENT_RENDERING_MODE = RenderingMode.SPRITE
    loader = AssetLoader(tile_size=8)
    
    # helper to access private method (if needed) or just trust public API
    # The 'missing_sprite' shouldn't exist
    sprite = loader.get_sprite("missing_entity")
    assert isinstance(sprite, pygame.Surface)
