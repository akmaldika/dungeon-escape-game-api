#!/usr/bin/env python3
"""
Pygame-based renderer for the roguelike game.
This replaces tcod's rendering while keeping tcod for FOV and pathfinding.
Provides pixel-perfect screenshots and exact tile size control.
"""

import pygame
import io
import os
from typing import Optional, List

# Game imports
from src.rendering.assets import AssetLoader
from src.rendering.ui import UIRenderer

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
        
        # Initialize sub-systems
        self.assets = AssetLoader(tile_size)
        self.ui = UIRenderer(width, height, tile_size, self.assets)
        
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
                
                tile_surface = None
                
                if game_map.visible[x, y]:
                    # Visible area
                    if game_map.tiles['walkable'][x, y]:
                        tile_surface = self.assets.get_sprite('floor')
                    elif tile_ch == ord(" "):  # Void tile
                        continue
                    else:
                        tile_surface = self.assets.get_sprite('wall')
                elif game_map.explored[x, y]:
                    # Explored but not visible
                    if game_map.tiles['walkable'][x, y]:
                        tile_surface = self.assets.get_sprite('dark_floor')
                    elif tile_ch == ord(" "):  # Void tile
                        continue
                    else:
                        tile_surface = self.assets.get_sprite('dark_wall')
                else:
                    # Unexplored 
                    if tile_ch == ord(" "):  # Void tile
                        continue
                    else:
                        tile_surface = self.assets.create_colored_tile((0, 0, 0)) # Shroud
                
                if tile_surface:
                    surface.blit(tile_surface, (pixel_x, pixel_y))
                
                # Render stairs if visible
                if (game_map.visible[x, y] and 
                    hasattr(game_map, 'downstairs_location') and 
                    (x, y) == game_map.downstairs_location):
                    stairs_surface = self.assets.get_sprite('ladder')
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
                
                if sprite_name:
                    surface.blit(self.assets.get_sprite(sprite_name), (pixel_x, pixel_y))
                else:
                    # Fallback to colored tile or text
                    entity_color = getattr(entity, 'color', (255, 255, 255))
                    if hasattr(entity, 'char') and isinstance(entity.char, str):
                        tile_surface = self.assets.create_text_tile(entity.char, entity_color)
                    else:
                        tile_surface = self.assets.create_colored_tile(entity_color)
                    surface.blit(tile_surface, (pixel_x, pixel_y))
    
    def render_ui(self, engine, surface: Optional[pygame.Surface] = None):
        """Render UI elements like health bar and messages."""
        if surface is None:
            surface = self.render_surface
        self.ui.render_ui(surface, engine)
    
    def render_main_menu(self, surface: Optional[pygame.Surface] = None):
        """Render the main menu."""
        if surface is None:
            surface = self.render_surface
        self.ui.render_main_menu(surface)
    
    def render_game_done_screen(self, surface: Optional[pygame.Surface] = None):
        """Render the game done screen (victory or completion)."""
        if surface is None:
            surface = self.render_surface
        self.ui.render_overlay_screen(surface, "GAME DONE", "Congratulations! You completed the challenge!", (255, 255, 255))
    
    def render_game_over_screen(self, surface: Optional[pygame.Surface] = None):
        """Render the game over screen (player died)."""
        if surface is None:
            surface = self.render_surface
        self.ui.render_overlay_screen(surface, "GAME OVER", "You have died!", (255, 100, 100))
    
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
            # Get raw pixel data
            raw_data = pygame.image.tostring(self.render_surface, 'RGB')
            
            # Create PIL Image
            from PIL import Image
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
            pygame.K_n: 110,  # tcod.event.KeySym.N
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
