from __future__ import annotations

from typing import TYPE_CHECKING, cast

import tcod
from tcod import libtcodpy

from src.core import color
from src.core.handlers.base import BaseEventHandler

if TYPE_CHECKING:
    from src.core.engine import Engine


class GameOverEventHandler(BaseEventHandler):
    """Handler for the game over screen."""
    
    def __init__(self, engine: Engine):
        self.engine = engine

    def on_render(self, console: tcod.console.Console) -> None:
        console.tiles_rgb["bg"] //= 8
        console.tiles_rgb["fg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2 - 3,
            "GAME DONE",
            fg=color.welcome_text,
            alignment=libtcodpy.CENTER,
        )
        
        console.print(
            console.width // 2,
            console.height // 2 - 1,
            "You have died!",
            fg=color.invalid,
            alignment=libtcodpy.CENTER,
        )
        
        console.print(
            console.width // 2,
            console.height // 2 + 1,
            "Press ESC or Q to return to main menu",
            fg=color.menu_text,
            alignment=libtcodpy.CENTER,
        )

    def ev_quit(self, event: tcod.event.Quit) -> None:
        pass

    def ev_keydown(self, event: tcod.event.KeyDown) -> BaseEventHandler | None:
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            try:
                from src.core.handlers.menus import MainMenu
            except Exception:
                # Fallback if import fails
                from src.core.handlers.menus import MainMenu
            return cast(BaseEventHandler, MainMenu())
        return None


class GameDoneEventHandler(BaseEventHandler):
    """Handler for the game completion screen."""
    
    def __init__(self, engine: Engine):
        self.engine = engine

    def on_render(self, console: tcod.console.Console) -> None:
        console.tiles_rgb["bg"] //= 8
        console.tiles_rgb["fg"] //= 8
        
        console.print(
            console.width // 2,
            console.height // 2 - 2,
            "GAME DONE",
            fg=color.welcome_text,
            alignment=libtcodpy.CENTER,
        )
        
        console.print(
            console.width // 2,
            console.height // 2,
            "Press ESC or Q to return to main menu",
            fg=color.menu_text,
            alignment=libtcodpy.CENTER,
        )
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> BaseEventHandler | None:
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            try:
                from src.core.handlers.menus import MainMenu
            except Exception:
                from src.core.handlers.menus import MainMenu
            return cast(BaseEventHandler, MainMenu())
        return None
