from __future__ import annotations

import pygame
from typing import TYPE_CHECKING, Optional, List

from src.core import color
from src.rendering.assets import AssetLoader

if TYPE_CHECKING:
    from src.core.engine import Engine

# UI Constants
# UI Constants
BAR_WIDTH_RATIO = 0.25  # 1/4 of screen width
BAR_HEIGHT_TILES = 1
BAR_BOTTOM_OFFSET = 5
MSG_X_OFFSET = 5
MSG_BOTTOM_OFFSET = 6
MSG_COUNT = 5

# Layout Coordinates (Tiles)
LAYOUT_HP_BAR_Y = 41
LAYOUT_HP_BAR_X = 0
LAYOUT_HP_BAR_WIDTH = 20
LAYOUT_LEVEL_Y = 43
LAYOUT_LEVEL_X = 0
LAYOUT_MSG_START_Y = 40
LAYOUT_MSG_X = 22
LAYOUT_MSG_HEIGHT = 5

class UIRenderer:
    """Handles rendering of UI elements (menus, HUD, messages)."""
    
    def __init__(self, width: int, height: int, tile_size: int, assets: AssetLoader):
        self.width = width # In tiles
        self.height = height # In tiles
        self.tile_size = tile_size
        self.pixel_width = width * tile_size
        self.pixel_height = height * tile_size
        self.assets = assets
        
        # Calculate dynamic spacing
        if tile_size <= 8:
            self.msg_line_spacing = 10 # Accommodate larger font
        else:
            self.msg_line_spacing = 40

    def render_ui(self, surface: pygame.Surface, engine: Engine) -> None:
        """Render UI elements like health bar and messages."""
        
        # 1. Health Bar
        bar_y = LAYOUT_HP_BAR_Y * self.tile_size
        bar_x = LAYOUT_HP_BAR_X * self.tile_size
        bar_width = LAYOUT_HP_BAR_WIDTH * self.tile_size
        bar_height = self.tile_size # 1 tile high
        
        # Background
        pygame.draw.rect(surface, color.bar_empty, (bar_x, bar_y, bar_width, bar_height))
        
        # Health fill
        if engine.player.fighter.max_hp > 0:
            fill_width = int(bar_width * engine.player.fighter.hp / engine.player.fighter.max_hp)
            pygame.draw.rect(surface, color.bar_filled, (bar_x, bar_y, fill_width, bar_height))
        
        # Health text (Centered on bar)
        if self.assets.font:
            health_text = f"HP: {engine.player.fighter.hp}/{engine.player.fighter.max_hp}"
            text_surface = self.assets.font.render(health_text, self.assets.antialias, color.bar_text)
            text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
            surface.blit(text_surface, text_rect)
            
        # 2. Dungeon Level
        if self.assets.font:
            level_text = f"Dungeon level: {engine.game_world.current_floor}"
            level_surface = self.assets.font.render(level_text, self.assets.antialias, color.white)
            # Align left
            surface.blit(level_surface, (LAYOUT_LEVEL_X * self.tile_size, LAYOUT_LEVEL_Y * self.tile_size))
        
        # 3. Messages
        if hasattr(engine, 'message_log') and engine.message_log.messages and self.assets.font:
            msg_x = LAYOUT_MSG_X * self.tile_size
            msg_start_y = LAYOUT_MSG_START_Y * self.tile_size
            
            # Show last N messages
            recent_messages = engine.message_log.messages[-LAYOUT_MSG_HEIGHT:]
            
            for i, message in enumerate(recent_messages):
                msg_y = msg_start_y + i * self.tile_size # 1 message per tile height
                msg_surface = self.assets.font.render(message.full_text[:80], self.assets.antialias, message.fg)
                surface.blit(msg_surface, (msg_x, msg_y))

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
        title_surface = self.assets.font_large.render(title_text, self.assets.antialias, (255, 255, 63))
        
        if self.tile_size == 16:
            title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 180))
        else:
            title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 80))
        # print(title_rect.size)
        surface.blit(title_surface, title_rect)
        
        # Author
        author_text = "By Akmal Mahardika Nurwahyu Pratama"
        author_surface = self.assets.font.render(author_text, self.assets.antialias, (255, 255, 63))
        
        if self.tile_size == 16:
            author_rect = author_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height - 40))
        else:
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
            option_surface = self.assets.font.render(option, self.assets.antialias, (255, 255, 255))
            margin = 30 
            if self.tile_size == 16:
                margin *= 2 
            option_rect = option_surface.get_rect(center=(center_x, start_y + i * margin))
            
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
        title_surface = self.assets.font_large.render(title, self.assets.antialias, title_color)
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 60))
        surface.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = self.assets.font.render(subtitle, self.assets.antialias, (255, 255, 255))
        subtitle_rect = subtitle_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 20))
        surface.blit(subtitle_surface, subtitle_rect)
        
        # Instructions
        instruction_text = "Press ESC or Q to return to main menu"
        instruction_surface = self.assets.font.render(instruction_text, self.assets.antialias, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 + 20))
        surface.blit(instruction_surface, instruction_rect)
