from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

from src.core import exceptions
from src.core.message_log import MessageLog

if TYPE_CHECKING:
	from src.core.entity import Actor
	from src.core.game_map import GameMap, GameWorld


class Engine:
	game_map: GameMap
	game_world: GameWorld

	def __init__(self, player: Actor):
		self.message_log = MessageLog(self)
		self.player = player
		self.step_counter = 0
		self.is_using_custom_map = False  # Add this flag
		self.game_done = False  # Game done flag
		self._current_step_messages = []  # Track messages for current step

	def start_new_step(self) -> None:
		"""Called at the beginning of each new step to reset message tracking."""
		self._current_step_messages = []
		self.step_counter += 1

	def add_step_message(self, message: str) -> None:
		"""Add a message that occurred in the current step with consecutive counting."""
		if self._current_step_messages and self._current_step_messages[-1]['text'] == message:
			self._current_step_messages[-1]['count'] += 1
		else:
			self._current_step_messages.append({'text': message, 'count': 1})

	def handle_enemy_turns(self) -> None:
		for entity in set(self.game_map.actors) - {self.player}:
			if entity.ai:
				try:
					entity.ai.perform()
				except exceptions.Impossible:
					pass  # Ignore impossible action exceptions from AI.

	def update_fov(self) -> None:
		"""Recompute the visible area based on the players point of view."""
		self.game_map.visible[:] = compute_fov(
			self.game_map.tiles["transparent"],
			(self.player.x, self.player.y),
			radius=8,
		)
		# If a tile is "visible" it should be added to "explored".
		self.game_map.explored |= self.game_map.visible

	def render(self, console: Console) -> None:
		self.game_map.render(console)
		self.last_console = console

		console_width = console.width
		console_height = console.height

		self.message_log.render(
			console=console,
			x=console_width // 4,
			y=console_height - 5,
			width=console_width // 2,
			height=5,
		)

	def get_current_level(self) -> int:
		return getattr(self.game_world, 'current_floor', 1)

	def get_player_tile_type(self) -> str:
		if self.game_done:
			return "-"
		x, y = self.player.x, self.player.y
		if hasattr(self.game_map, 'downstairs_location') and (x, y) == self.game_map.downstairs_location:
			return "ladder/stairs"
		for item in self.game_map.items:
			if item.x == x and item.y == y:
				return f"item({item.name}) (press 'g' to pick up)"
		return "floor"

