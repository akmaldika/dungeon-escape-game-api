from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

from src.core.handlers.base import ActionOrHandler
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
