from __future__ import annotations

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union, cast

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
	from src.core.entity import Item


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
	def handle_events(self, event: tcod.event.Event) -> 'BaseEventHandler':
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

	def handle_action(self, action: Optional[Action]) -> bool:
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
	def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
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

	def on_exit(self) -> Optional[ActionOrHandler]:
		return MainGameEventHandler(self.engine)


class MainGameEventHandler(EventHandler):
	def use_health_potion(self) -> Optional[ActionOrHandler]:
		player = self.engine.player
		inventory = player.inventory
        
		for item in inventory.items:
			if getattr(item, 'consumable', None) and "Health Potion" in item.name:
				if item.consumable is not None:
					return item.consumable.get_action(player)
        
		self.engine.message_log.add_message("You don't have any health potions!", color.impossible)
		return None

	def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
		action: Optional[Action] = None
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
			try:
				from src.app.setup_game import MainMenu
			except Exception:
				from setup_game import MainMenu
			return cast(BaseEventHandler, MainMenu())
		elif key == tcod.event.KeySym.G:
			action = PickupAction(player)
		elif key == tcod.event.KeySym.I:
			return self.use_health_potion()
		return action


class GameOverEventHandler(EventHandler):
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

	def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
		if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
			try:
				from src.app.setup_game import MainMenu
			except Exception:
				from setup_game import MainMenu
			return cast(BaseEventHandler, MainMenu())
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
    
	def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
		if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
			try:
				from src.app.setup_game import MainMenu
			except Exception:
				from setup_game import MainMenu
			return cast(BaseEventHandler, MainMenu())
		return None

