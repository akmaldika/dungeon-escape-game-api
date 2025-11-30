from __future__ import annotations

from typing import TYPE_CHECKING, Union, cast

import tcod
from tcod import libtcodpy

from src.core import actions
from src.core.actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
)
from src.core import color
from src.core import exceptions

if TYPE_CHECKING:
    from src.core.engine import Engine

MOVE_KEYS = {
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.W: (0, -1),
    tcod.event.KeySym.S: (0, 1),
    tcod.event.KeySym.A: (-1, 0),
    tcod.event.KeySym.D: (1, 0),
}

WAIT_KEYS = {
    tcod.event.KeySym.PERIOD,
    tcod.event.KeySym.KP_5,
    tcod.event.KeySym.CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,
    tcod.event.KeySym.KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    """Base class for all event handlers."""
    
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.console.Console) -> None:
        """Render the screen for this handler."""
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Action | None:
        """Handle quit event."""
        raise SystemExit()


class EventHandler(BaseEventHandler):
    """Main event handler for the game."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events and process actions."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        
        if action_or_state is not None:
            self.engine.start_new_step()
        
        action_performed = self.handle_action(action_or_state)
        
        if action_performed:
            if self.engine.game_done:
                return GameDoneEventHandler(self.engine)
            elif not self.engine.player.is_alive:
                return GameOverEventHandler(self.engine)
            return MainGameEventHandler(self.engine)
        return self

    def handle_action(self, action: Action | None) -> bool:
        """Perform an action and return True if it was successful."""
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        
        return True

    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)


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


class MainGameEventHandler(EventHandler):
    """Handler for the main game loop."""
    
    def use_health_potion(self) -> ActionOrHandler | None:
        player = self.engine.player
        inventory = player.inventory
        
        for item in inventory.items:
            if getattr(item, 'consumable', None) and "Health Potion" in item.name:
                if item.consumable is not None:
                    return item.consumable.get_action(player)
        
        self.engine.message_log.add_message("You don't have any health potions!", color.impossible)
        return None

    def ev_keydown(self, event: tcod.event.KeyDown) -> ActionOrHandler | None:
        action: Action | None = None
        key = event.sym
        
        player = self.engine.player
        
        if key == tcod.event.KeySym.SPACE:
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.KeySym.ESCAPE:
            try:
                from src.app.setup_game import MainMenu
            except Exception:
                # Fallback if import fails (shouldn't happen with correct structure)
                from src.app.setup_game import MainMenu
            return cast(BaseEventHandler, MainMenu())
        elif key == tcod.event.KeySym.G:
            action = PickupAction(player)
        elif key == tcod.event.KeySym.I:
            return self.use_health_potion()
        return action


class GameOverEventHandler(EventHandler):
    """Handler for the game over screen."""
    
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
                from src.app.setup_game import MainMenu
            except Exception:
                from src.app.setup_game import MainMenu
            return cast(BaseEventHandler, MainMenu())
        return None


class GameDoneEventHandler(EventHandler):
    """Handler for the game completion screen."""
    
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
                from src.app.setup_game import MainMenu
            except Exception:
                from src.app.setup_game import MainMenu
            return cast(BaseEventHandler, MainMenu())
        return None
