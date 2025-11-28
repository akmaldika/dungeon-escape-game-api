#!/usr/bin/env python3
"""
Pygame-based renderer for the roguelike game.
This replaces tcod's rendering while keeping tcod for FOV and pathfinding.
Provides pixel-perfect screenshots and exact tile size control.
"""

import pygame
import numpy as np
from PIL import Image
import io
import os
from typing import Dict, Tuple, Optional, List

# Game imports
try:
    from src.core import color, tile_types, entity_factories
    from src.core.render_order import RenderOrder
    from src.api.sprite_config import get_sprite_directory, DEFAULT_SPRITE_SIZE # type: ignore #
except Exception:
    # Fallback during migration
    import color
    import tile_types
    import entity_factories
    from render_order import RenderOrder
    # Inline fallback for sprite config during development/migration
    DEFAULT_SPRITE_SIZE = 16
    def get_sprite_directory(sprite_size):
        return "assets/16x16" if sprite_size == 16 else "assets/8x8"

class PygameRenderer:
    """Pygame-based renderer for the game."""
    
    def __init__(self, width: int, height: int, tile_size: int = 16, headless: bool = False):
        """
        Initialize the pygame renderer.
        
        Args:
            width: Number of tiles horizontally
            height: Number of tiles vertically  
            tile_size: Size of each tile in pixels (16x16 recommended for models)
            headless: If True, runs without a window (for AI training/benchmarking)
        """
        self.headless = headless
        if self.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        pygame.font.init()
        
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.pixel_width = width * tile_size
        self.pixel_height = height * tile_size
        
        # Create the display surface
        self.screen = pygame.display.set_mode((self.pixel_width, self.pixel_height))
        pygame.display.set_caption("Dungeon Escape AI - Pygame Renderer")
        
        # Create a surface for off-screen rendering (for screenshots)
        self.render_surface = pygame.Surface((self.pixel_width, self.pixel_height))
        
        # Load fonts with better sizes
        # self.font_small = pygame.font.Font(None, max(16, tile_size))  # Larger font
        self.font_small = pygame.font.Font(None, max(24, tile_size))  # Larger font
        self.font_large = pygame.font.Font(None, max(32, tile_size + 8))  # Even larger for titles
        self.font = self.font_small  # Default font
        
        # Load sprites and tiles
        self.sprites = {}
        self.tiles = {}
        
        self._load_assets()
        
        # Colors for tiles and entities
        self.color_map = {
            'wall_light': (130, 110, 50),
            'wall_dark': (0, 0, 100),
            'floor_light': (200, 180, 50),
            'floor_dark': (50, 50, 150),
            'stairs': (255, 255, 0),
            'shroud': (0, 0, 0),
            'player': (255, 255, 255),
            'ghost': (63, 127, 63),
            'red_ghost': (0, 127, 0),
            'health_potion': (127, 0, 255),
        }
        
    def _load_assets(self):
        """Load all sprites and tile images from the appropriate directory."""
        use_graphics = True
        
        # Get sprite directory based on tile_size
        sprite_dir = get_sprite_directory(self.tile_size)
        
        # Asset paths - dynamically built based on sprite directory
        sprite_names = [
            'player', 'ghost', 'red_ghost', 'floor', 'dark_floor',
            'wall', 'dark_wall', 'ladder', 'wooden_box',
        ]
        sprite_paths = {
            name: f'{sprite_dir}/{name}.png'
            for name in sprite_names
        }
        
        # Load sprites if using graphics
        if use_graphics:
            for name, path in sprite_paths.items():
                if os.path.exists(path):
                    try:
                        # Load and scale to exact tile size
                        image = pygame.image.load(path)
                        scaled_image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
                        self.sprites[name] = scaled_image
                    except Exception as e:
                        print(f"Failed to load sprite {name}: {e}")
                        # Create fallback colored rectangle
                        self.sprites[name] = self._create_colored_tile((128, 128, 128))
        
        # Create fallback tiles (colored rectangles) for missing sprites
        fallback_tiles = {
            'player': (255, 255, 255),
            'ghost': (63, 127, 63),
            'red_ghost': (0, 127, 0),
            'floor': (200, 180, 50),
            'dark_floor': (50, 50, 150),
            'wall': (130, 110, 50),
            'dark_wall': (0, 0, 100),
            'ladder': (255, 255, 0),
            'wooden_box': (127, 0, 255),
        }
        
        for name, color in fallback_tiles.items():
            if name not in self.sprites:
                self.sprites[name] = self._create_colored_tile(color)
    
    def _create_colored_tile(self, color: Tuple[int, int, int]) -> pygame.Surface:
        """Create a colored rectangle tile."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(color)
        return surface
    
    def _create_text_tile(self, char: str, color: Tuple[int, int, int], bg_color: Tuple[int, int, int] = (0, 0, 0)) -> pygame.Surface:
        """Create a tile with a character."""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(bg_color)
        
        text_surface = self.font.render(char, True, color)
        # Center the text
        text_rect = text_surface.get_rect(center=(self.tile_size // 2, self.tile_size // 2))
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def clear(self, surface: Optional[pygame.Surface] = None):
        """Clear the rendering surface."""
        if surface is None:
            surface = self.render_surface
        surface.fill((0, 0, 0))  # Black background
    
    def render_game_map(self, game_map, surface: Optional[pygame.Surface] = None):
        """Render the game map."""
        if surface is None:
            surface = self.render_surface
        
        # Render tiles
        for x in range(min(self.width, game_map.width)):
            for y in range(min(self.height, game_map.height)):
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Determine what to render
                tile_ch = game_map.tiles['light']['ch'][x, y] if game_map.visible[x, y] else game_map.tiles['dark']['ch'][x, y]
                
                if game_map.visible[x, y]:
                    # Visible area
                    if game_map.tiles['walkable'][x, y]:
                        # Floor
                        tile_surface = self.sprites.get('floor', self._create_colored_tile(self.color_map['floor_light']))
                    elif tile_ch == ord(" "):  # Void tile (space character)
                        # Void - render as black (skip rendering)
                        continue
                    else:
                        # Wall
                        tile_surface = self.sprites.get('wall', self._create_colored_tile(self.color_map['wall_light']))
                elif game_map.explored[x, y]:
                    # Explored but not visible
                    if game_map.tiles['walkable'][x, y]:
                        # Dark floor
                        tile_surface = self.sprites.get('dark_floor', self._create_colored_tile(self.color_map['floor_dark']))
                    elif tile_ch == ord(" "):  # Void tile (space character)
                        # Void - render as black (skip rendering)
                        continue
                    else:
                        # Dark wall
                        tile_surface = self.sprites.get('dark_wall', self._create_colored_tile(self.color_map['wall_dark']))
                else:
                    # Unexplored 
                    if tile_ch == ord(" "):  # Void tile (space character)
                        # Void - render as black (skip rendering)
                        continue
                    else:
                        # Shroud
                        tile_surface = self._create_colored_tile(self.color_map['shroud'])
                
                surface.blit(tile_surface, (pixel_x, pixel_y))
                
                # Render stairs if visible
                if (game_map.visible[x, y] and 
                    hasattr(game_map, 'downstairs_location') and 
                    (x, y) == game_map.downstairs_location):
                    stairs_surface = self.sprites.get('ladder', self._create_colored_tile(self.color_map['stairs']))
                    surface.blit(stairs_surface, (pixel_x, pixel_y))
    
    def render_entities(self, game_map, surface: Optional[pygame.Surface] = None):
        """Render all entities in the game map."""
        if surface is None:
            surface = self.render_surface
        
        # Sort entities by render order
        entities_sorted = sorted(game_map.entities, key=lambda x: x.render_order.value)
        
        for entity in entities_sorted:
            if (entity.x < self.width and entity.y < self.height and 
                game_map.visible[entity.x, entity.y]):
                
                pixel_x = entity.x * self.tile_size
                pixel_y = entity.y * self.tile_size
                
                # Get sprite for entity
                sprite_name = None
                if entity.name == "Player":
                    sprite_name = 'player'
                elif entity.name == "Ghost":
                    sprite_name = 'ghost'
                elif entity.name == "Red Ghost":
                    sprite_name = 'red_ghost'
                elif "Health Potion" in entity.name:
                    sprite_name = 'wooden_box'
                
                if sprite_name and sprite_name in self.sprites:
                    surface.blit(self.sprites[sprite_name], (pixel_x, pixel_y))
                else:
                    # Fallback to colored tile
                    entity_color = getattr(entity, 'color', (255, 255, 255))
                    if hasattr(entity, 'char') and isinstance(entity.char, str):
                        # Text-based entity
                        tile_surface = self._create_text_tile(entity.char, entity_color)
                    else:
                        # Colored rectangle
                        tile_surface = self._create_colored_tile(entity_color)
                    surface.blit(tile_surface, (pixel_x, pixel_y))
    
    def render_ui(self, engine, surface: Optional[pygame.Surface] = None):
        """Render UI elements like health bar and messages."""
        if surface is None:
            surface = self.render_surface
        
        # Health bar
        bar_width = self.width // 4 * self.tile_size
        bar_height = self.tile_size
        bar_x = 0
        bar_y = self.pixel_height - 5 * self.tile_size
        
        # Background
        pygame.draw.rect(surface, color.bar_empty, (bar_x, bar_y, bar_width, bar_height))
        
        # Health fill
        if engine.player.fighter.max_hp > 0:
            fill_width = int(bar_width * engine.player.fighter.hp / engine.player.fighter.max_hp)
            pygame.draw.rect(surface, color.bar_filled, (bar_x, bar_y, fill_width, bar_height))
        
        # Health text
        health_text = f"HP: {engine.player.fighter.hp}/{engine.player.fighter.max_hp}"
        text_surface = self.font.render(health_text, True, color.bar_text)
        surface.blit(text_surface, (bar_x + 5, bar_y + 2))
        
        # Dungeon level
        level_text = f"Dungeon level: {engine.game_world.current_floor}"
        level_surface = self.font.render(level_text, True, color.white)
        surface.blit(level_surface, (0, self.pixel_height - 3 * self.tile_size))
        
        # Messages
        if hasattr(engine, 'message_log') and engine.message_log.messages:
            msg_x = self.width // 4 * self.tile_size + 5
            msg_y = self.pixel_height - 6 * self.tile_size
            msg_width = self.width // 2 * self.tile_size
            
            # Show last few messages (increased to 6 to show more)
            recent_messages = engine.message_log.messages[-6:]  # Last 6 messages
            for i, message in enumerate(recent_messages):
                # Show stacked count using full_text (e.g., "That way is blocked. (x3)")
                msg_surface = self.font.render(message.full_text[:80], True, message.fg)  # Truncate long messages
                surface.blit(msg_surface, (msg_x, msg_y + i * 20))  # Increased line spacing
    
    def render_main_menu(self, surface: Optional[pygame.Surface] = None):
        """Render the main menu."""
        if surface is None:
            surface = self.render_surface
        
        self.clear(surface)
        
        # Load background image if available
        try:
            bg_image = pygame.image.load("assets/menu_background.png")
            bg_image = pygame.transform.scale(bg_image, (self.pixel_width, self.pixel_height))
            surface.blit(bg_image, (0, 0))
        except:
            # Fallback to dark background
            surface.fill((20, 20, 40))
        
        # Title
        title_text = "TOMBS OF ANCIENT AI AGENT"
        title_surface = self.font_large.render(title_text, True, (255, 255, 63))  # Pale yellow
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 80))
        surface.blit(title_surface, title_rect)
        
        # Author
        author_text = "By Akmal Mahardika Nurwahyu Pratama"
        author_surface = self.font.render(author_text, True, (255, 255, 63))
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
            option_surface = self.font.render(option, True, (255, 255, 255))
            option_rect = option_surface.get_rect(center=(center_x, start_y + i * 30))
            
            # Draw background box
            bg_rect = option_rect.inflate(20, 10)
            pygame.draw.rect(surface, (0, 0, 0, 64), bg_rect)
            pygame.draw.rect(surface, (100, 100, 100), bg_rect, 2)
            
            surface.blit(option_surface, option_rect)
    
    def render_game_done_screen(self, surface: Optional[pygame.Surface] = None):
        """Render the game done screen (victory or completion) - full screen overlay."""
        if surface is None:
            surface = self.render_surface
        
        # Fill entire screen with black background
        surface.fill((0, 0, 0))
        
        # Main title
        title_text = "GAME DONE"
        title_surface = self.font_large.render(title_text, True, (255, 255, 255))  # White text
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 60))
        surface.blit(title_surface, title_rect)
        
        # Subtitle message
        subtitle_text = "Congratulations! You completed the challenge!"
        subtitle_surface = self.font.render(subtitle_text, True, (255, 255, 255))  # White text
        subtitle_rect = subtitle_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 20))
        surface.blit(subtitle_surface, subtitle_rect)
        
        # Instructions
        instruction_text = "Press ESC or Q to return to main menu"
        instruction_surface = self.font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 + 20))
        surface.blit(instruction_surface, instruction_rect)
    
    def render_game_over_screen(self, surface: Optional[pygame.Surface] = None):
        """Render the game over screen (player died) - full screen overlay."""
        if surface is None:
            surface = self.render_surface
        
        # Fill entire screen with black background
        surface.fill((0, 0, 0))
        
        # Main title
        title_text = "GAME OVER"
        title_surface = self.font_large.render(title_text, True, (255, 100, 100))  # Red text
        title_rect = title_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 60))
        surface.blit(title_surface, title_rect)
        
        # Subtitle message
        subtitle_text = "You have died!"
        subtitle_surface = self.font.render(subtitle_text, True, (255, 255, 255))  # White text
        subtitle_rect = subtitle_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 - 20))
        surface.blit(subtitle_surface, subtitle_rect)
        
        # Instructions
        instruction_text = "Press ESC or Q to return to main menu"
        instruction_surface = self.font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(self.pixel_width // 2, self.pixel_height // 2 + 20))
        surface.blit(instruction_surface, instruction_rect)
    
    def render_complete(self, engine, surface: Optional[pygame.Surface] = None):
        """Render the complete game state."""
        if surface is None:
            surface = self.render_surface
        
        self.clear(surface)
        
        if hasattr(engine, 'game_map'):
            self.render_game_map(engine.game_map, surface)
            self.render_entities(engine.game_map, surface)
        
        self.render_ui(engine, surface)
    
    def present(self):
        """Present the rendered surface to the screen."""
        if not self.headless:
            self.screen.blit(self.render_surface, (0, 0))
            pygame.display.flip()
    
    def get_screenshot_bytes(self) -> bytes:
        """Get screenshot as raw PNG bytes with exact pixel dimensions."""
        try:
            # Convert pygame surface to PIL Image
            # Get raw pixel data
            raw_data = pygame.image.tostring(self.render_surface, 'RGB')
            
            # Create PIL Image
            img = Image.frombytes('RGB', (self.pixel_width, self.pixel_height), raw_data)
            
            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
        except Exception as e:
            print(f"Screenshot error: {e}")
            return b''
    
    def handle_events(self) -> List[pygame.event.Event]:
        """Get pygame events and return them."""
        return pygame.event.get()
    
    def quit(self):
        """Clean up pygame resources."""
        pygame.quit()


class PygameEventConverter:
    """Convert pygame events to tcod-like events for compatibility."""
    
    @staticmethod
    def pygame_to_tcod_key(pygame_key: int) -> Optional[int]:
        """Convert pygame key to tcod KeySym equivalent."""
        key_mapping = {
            pygame.K_w: 119,  # tcod.event.KeySym.W
            pygame.K_a: 97,   # tcod.event.KeySym.A
            pygame.K_s: 115,  # tcod.event.KeySym.S
            pygame.K_d: 100,  # tcod.event.KeySym.D
            pygame.K_n: 110,  # tcod.event.KeySym.N - FIXED!
            pygame.K_UP: 1073741906,     # tcod.event.KeySym.UP
            pygame.K_DOWN: 1073741905,   # tcod.event.KeySym.DOWN
            pygame.K_LEFT: 1073741904,   # tcod.event.KeySym.LEFT
            pygame.K_RIGHT: 1073741903,  # tcod.event.KeySym.RIGHT
            pygame.K_SPACE: 32,          # tcod.event.KeySym.SPACE
            pygame.K_g: 103,             # tcod.event.KeySym.G
            pygame.K_i: 105,             # tcod.event.KeySym.I
            pygame.K_PERIOD: 46,         # tcod.event.KeySym.PERIOD
            pygame.K_ESCAPE: 27,         # tcod.event.KeySym.ESCAPE
            pygame.K_q: 113,             # tcod.event.KeySym.Q
        }
        return key_mapping.get(pygame_key)
    
    @staticmethod
    def create_tcod_key_event(pygame_key: int, pygame_mods: int):
        """Create a tcod-compatible key event from pygame event."""
        import tcod.event
        
        tcod_key = PygameEventConverter.pygame_to_tcod_key(pygame_key)
        if tcod_key is None:
            return None
        
        # Convert modifiers
        tcod_mod = tcod.event.Modifier(0)
        if pygame_mods & pygame.KMOD_SHIFT:
            tcod_mod |= tcod.event.Modifier.SHIFT
        if pygame_mods & pygame.KMOD_CTRL:
            tcod_mod |= tcod.event.Modifier.CTRL
        if pygame_mods & pygame.KMOD_ALT:
            tcod_mod |= tcod.event.Modifier.ALT
        
        return tcod.event.KeyDown(
            sym=tcod_key,
            mod=tcod_mod,
            scancode=0
        )
