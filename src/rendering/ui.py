from __future__ import annotations

import pygame
from typing import TYPE_CHECKING, Optional, List

from src.core import color
from src.rendering.assets import AssetLoader

if TYPE_CHECKING:
    from src.core.engine import Engine

# UI Constants
BAR_WIDTH_RATIO = 0.25  # 1/4 of screen width
BAR_HEIGHT_TILES = 1
BAR_BOTTOM_OFFSET = 5
MSG_X_OFFSET = 5
MSG_BOTTOM_OFFSET = 6
MSG_LINE_SPACING = 20
MSG_COUNT = 5

class UIRenderer:
    """Handles rendering of UI elements (menus, HUD, messages)."""
    
    def __init__(self, width: int, height: int, tile_size: int, assets: AssetLoader):
        self.width = width # In tiles
        self.height = height # In tiles
        self.tile_size = tile_size
        self.pixel_width = width * tile_size
        self.pixel_height = height * tile_size
        self.assets = assets

    def render_ui(self, surface: pygame.Surface, engine: Engine) -> None:
        """Render UI elements like health bar and messages."""
        # Health bar
        bar_width = int(self.width * BAR_WIDTH_RATIO * self.tile_size)
        bar_height = self.tile_size * BAR_HEIGHT_TILES
        bar_x = 0
        bar_y = self.pixel_height - BAR_BOTTOM_OFFSET * self.tile_size
        
        # Background
        pygame.draw.rect(surface, color.bar_empty, (bar_x, bar_y, bar_width, bar_height))
        
        # Health fill
        if engine.player.fighter.max_hp > 0:
            fill_width = int(bar_width * engine.player.fighter.hp / engine.player.fighter.max_hp)
            pygame.draw.rect(surface, color.bar_filled, (bar_x, bar_y, fill_width, bar_height))
        
        # Health text
        if self.assets.font:
            health_text = f"HP: {engine.player.fighter.hp}/{engine.player.fighter.max_hp}"
            text_surface = self.assets.font.render(health_text, True, color.bar_text)
            surface.blit(text_surface, (bar_x + 5, bar_y + 2))
            
            # Dungeon level
            level_text = f"Dungeon level: {engine.game_world.current_floor}"
            level_surface = self.assets.font.render(level_text, True, color.white)
            surface.blit(level_surface, (0, self.pixel_height - 3 * self.tile_size))
        
        # Messages
        if hasattr(engine, 'message_log') and engine.message_log.messages and self.assets.font:
            msg_x = int(self.width * BAR_WIDTH_RATIO * self.tile_size) + MSG_X_OFFSET
            msg_y = self.pixel_height - MSG_BOTTOM_OFFSET * self.tile_size
            
            # Show last few messages
            recent_messages = engine.message_log.messages[-MSG_COUNT:]
            for i, message in enumerate(recent_messages):
                msg_surface = self.assets.font.render(message.full_text[:80], True, message.fg)
                surface.blit(msg_surface, (msg_x, msg_y + i * MSG_LINE_SPACING))

    def render_main_menu(self, surface: pygame.Surface) -> None:
        """Render the main menu."""
        surface.fill((0, 0, 0)) # Clear
        
        # Load background image if available
        try:
            bg_image = pygame.image.load("assets/menu_background.png")
            bg_image = pygame.transform.scale(bg_image, (self.pixel_width, self.pixel_height))
            surface.blit(bg_image, (0, 0))
        except:
            # Fallback to dark background
            surface.fill((20, 20, 40))
        
        if not self.assets.font_large or not self.assets.font:
            return

        # Title
        title_text = "TOMBS OF ANCIENT AI AGENT"
        title_surface = self.assets.font_large.render(title_text, True, (255, 255, 63))
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 80))
        surface.blit(title_surface, title_rect)
        
        # Author
        author_text = "By Akmal Mahardika Nurwahyu Pratama"
        author_surface = self.assets.font.render(author_text, True, (255, 255, 63))
        author_rect = author_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height - 40))
        surface.blit(author_surface, author_rect)
        
        # Menu options
        menu_options = [
            "[N] Play a new game",
            "[S] Static map test", 
            "[Q] Quit",
        ]
        
        center_x = self.pixel_width // 2
        start_y = self.pixel_height // 2 - 20
        
        for i, option in enumerate(menu_options):
            option_surface = self.assets.font.render(option, True, (255, 255, 255))
            option_rect = option_surface.get_rect(center=(center_x, start_y + i * 30))
            
            # Draw background box
            bg_rect = option_rect.inflate(20, 10)
            pygame.draw.rect(surface, (0, 0, 0, 64), bg_rect)
            pygame.draw.rect(surface, (100, 100, 100), bg_rect, 2)
            
            surface.blit(option_surface, option_rect)

    def render_overlay_screen(self, surface: pygame.Surface, title: str, subtitle: str, title_color: Tuple[int, int, int]) -> None:
        """Generic overlay screen renderer (Game Over, Game Done)."""
        surface.fill((0, 0, 0))
        
        if not self.assets.font_large or not self.assets.font:
            return

        # Main title
        title_surface = self.assets.font_large.render(title, True, title_color)
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 60))
        surface.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = self.assets.font.render(subtitle, True, (255, 255, 255))
        subtitle_rect = subtitle_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 20))
        surface.blit(subtitle_surface, subtitle_rect)
        
        # Instructions
        instruction_text = "Press ESC or Q to return to main menu"
        instruction_surface = self.assets.font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 + 20))
        surface.blit(instruction_surface, instruction_rect)
