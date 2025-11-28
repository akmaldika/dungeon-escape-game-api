"""
Sprite and rendering configuration.
Supports both 8px and 16px sprite sets.
"""

from __future__ import annotations

import os
from typing import Literal


# Default sprite pixel size (can be 8 or 16)
DEFAULT_SPRITE_SIZE: Literal[8, 16] = 16

# Supported sprite sizes
SUPPORTED_SPRITE_SIZES = [8, 16]

# Sprite directory mapping
SPRITE_DIRECTORIES = {
    8: "assets/8x8",
    16: "assets/16x16",
}


def get_sprite_directory(sprite_size: int) -> str:
    """Get the sprite directory for a given sprite size.
    
    Args:
        sprite_size: Either 8 or 16 (pixels)
    
    Returns:
        Path to the sprite directory
        
    Raises:
        ValueError: If sprite_size is not supported
    """
    if sprite_size not in SUPPORTED_SPRITE_SIZES:
        raise ValueError(
            f"Unsupported sprite size: {sprite_size}. "
            f"Supported sizes: {SUPPORTED_SPRITE_SIZES}"
        )
    return SPRITE_DIRECTORIES[sprite_size]


def validate_sprite_directory(sprite_size: int) -> bool:
    """Check if sprite directory exists for the given size.
    
    Args:
        sprite_size: Either 8 or 16 (pixels)
    
    Returns:
        True if directory exists, False otherwise
    """
    sprite_dir = get_sprite_directory(sprite_size)
    return os.path.isdir(sprite_dir)


__all__ = [
    "DEFAULT_SPRITE_SIZE",
    "SUPPORTED_SPRITE_SIZES",
    "SPRITE_DIRECTORIES",
    "get_sprite_directory",
    "validate_sprite_directory",
]
