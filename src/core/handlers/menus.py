from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from src.core.handlers.base import ActionOrHandler, BaseEventHandler
from src.core.handlers.game import EventHandler, MainGameEventHandler

if TYPE_CHECKING:
    from src.core.engine import Engine


class AskUserEventHandler(EventHandler):
    """Handler for asking user input (e.g. menus)."""
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        if event.sym in {
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def on_exit(self) -> ActionOrHandler | None:
        return MainGameEventHandler(self.engine)


# Load the background image with Pillow and ensure it's RGB (no alpha channel).
# This is used by MainMenu, so we load it here or in a resource loader.
# For now, keeping it simple as in the original setup_game.py
from PIL import Image
import numpy as np
from tcod import libtcodpy
from src.core import color
# import src.core.input_handlers as input_handlers # REMOVED to avoid circular import

try:
    bg_img = Image.open("assets/menu_background.png").convert("RGB")
    background_image = np.asarray(bg_img, dtype=np.uint8)
except Exception:
    # Fallback if image not found
    background_image = np.zeros((10, 10, 3), dtype=np.uint8)


class MainMenu(BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.console.Console) -> None:
        """Render the main menu on a background image."""
        if background_image.shape[0] > 10: # Check if real image loaded
            console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF ANCIENT AI AGENT",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "By Akmal Mahardika Nurwahyu Pratama",
            fg=color.menu_title,
            alignment=libtcodpy.CENTER,
        )

        menu_width = 30
        for i, text in enumerate([
            "[N] Play a new game",
            "[S] Static map test",
            "[Q] Quit",
        ]):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=libtcodpy.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> ActionOrHandler | None:
        from src.core.setup import new_game # Delayed import to avoid circular dependency
        
        if event.sym in (tcod.event.KeySym.Q, tcod.event.KeySym.ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.KeySym.N:
            return MainGameEventHandler(new_game(use_custom_map=False))
        elif event.sym == tcod.event.KeySym.S:
            # Test static map
            test_map = "custom_map.txt"
            return MainGameEventHandler(new_game(use_custom_map=True, custom_map_file=test_map))

        return None
