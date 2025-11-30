from __future__ import annotations

from typing import TYPE_CHECKING, cast

import tcod

from src.core import actions, color, exceptions
from src.core.actions import Action, BumpAction, PickupAction, WaitAction
from src.core.handlers.base import BaseEventHandler, ActionOrHandler, MOVE_KEYS, WAIT_KEYS
from src.core.handlers.death import GameDoneEventHandler, GameOverEventHandler

if TYPE_CHECKING:
    from src.core.engine import Engine


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
                from src.app.setup_game import MainMenu
            return cast(BaseEventHandler, MainMenu())
        elif key == tcod.event.KeySym.G:
            action = PickupAction(player)
        elif key == tcod.event.KeySym.I:
            return self.use_health_potion()
        return action
