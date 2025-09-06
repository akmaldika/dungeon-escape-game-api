from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod

from tcod import libtcodpy

import actions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item


MOVE_KEYS = {
    # Arrow keys.
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    
    # WASD
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
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.console.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        
        # Start new step BEFORE performing action (if there is an action)
        if action_or_state is not None:
            self.engine.start_new_step()
        
        # Handle the action first
        action_performed = self.handle_action(action_or_state)
        
        if action_performed:
            # Auto check for stairs after any action, turned off for now
            # self.check_stairs()
            
            # Check if game is done (custom map completed)
            if self.engine.game_done:
                return GameDoneEventHandler(self.engine)
            # Check if player died
            elif not self.engine.player.is_alive:
                return GameOverEventHandler(self.engine)
            return MainGameEventHandler(self.engine)
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods."""
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        
        return True

    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
        
    def check_stairs(self) -> None:
        """Automatically take stairs if player is standing on them."""
        player = self.engine.player
        if (player.x, player.y) == self.engine.game_map.downstairs_location:
            # Check if using custom map
            if self.engine.is_using_custom_map:
                # End game for custom map
                self.engine.message_log.add_message(
                    "You have completed the map! Game Done.", color.welcome_text
                )
                self.engine.game_done = True
            else:
                # Normal behavior for procedural maps
                self.engine.game_world.generate_floor()
                
                # Get new dungeon level for scaling
                new_dungeon_level = self.engine.game_world.current_floor
                
                # Apply dungeon level scaling (increases max HP)
                player.fighter.apply_dungeon_level_scaling(new_dungeon_level)
                
                # Restore 50% of current max health when going to next level
                heal_amount = int(player.fighter.max_hp * 0.5)
                player.fighter.hp = min(
                    player.fighter.hp + heal_amount,
                    player.fighter.max_hp
                )
                
                self.engine.message_log.add_message(
                    "You descend the staircase.", color.descend
                )
                self.engine.message_log.add_message(
                    f"You feel refreshed! Restored {heal_amount} health.", color.health_recovered
                )
                self.engine.update_fov()  # Update FOV for new floor


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class MainGameEventHandler(EventHandler):
    def use_health_potion(self) -> Optional[ActionOrHandler]:
        """Try to use the first health potion in the inventory."""
        player = self.engine.player
        inventory = player.inventory
        
        # Look for a health potion in the inventory
        for item in inventory.items:
            if item.consumable and "Health Potion" in item.name:
                # Return the action to use this item
                return item.consumable.get_action(player)
        
        # No health potion found
        self.engine.message_log.add_message("You don't have any health potions!", color.impossible)
        return None

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None
        # print(f"Key pressed: {event.sym}, mod: {event.mod}")

        key = event.sym
        modifier = event.mod

        player = self.engine.player
        
        if key == tcod.event.KeySym.SPACE:
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.KeySym.ESCAPE:
            # Return to main menu instead of quitting
            from setup_game import MainMenu
            return MainMenu()

        elif key == tcod.event.KeySym.G:
            action = PickupAction(player)

        elif key == tcod.event.KeySym.I:
            return self.use_health_potion()
        # No valid key was pressed
        return action

class GameOverEventHandler(EventHandler):
    def on_render(self, console: tcod.console.Console) -> None:
        """Render the game over screen with Game Done message."""
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

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            from setup_game import MainMenu
            return MainMenu()
        return None


CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
    tcod.event.KeySym.W: -1,
    tcod.event.KeySym.S: 1,
    tcod.event.KeySym.PAGEUP: -10,
    tcod.event.KeySym.PAGEDOWN: 10,
}


class GameDoneEventHandler(EventHandler):
    """Handle the game done screen when custom map is completed or player dies."""
    
    def on_render(self, console: tcod.console.Console) -> None:
        """Render the game done screen."""
        # Dim the background
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
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Handle key presses on game done screen."""
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            # Return to main menu
            from setup_game import MainMenu
            return MainMenu()
        return None


