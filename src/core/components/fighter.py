from __future__ import annotations

from typing import TYPE_CHECKING

from src.core import color
from src.core.components.base_component import BaseComponent
from src.core.render_order import RenderOrder

if TYPE_CHECKING:
	from src.core.entity import Actor


class Fighter(BaseComponent["Actor"]):

	def __init__(self, hp: int, base_power: int):
		self.max_hp = hp
		self._hp = hp
		self.base_power = base_power

	@property
	def hp(self) -> int:
		return self._hp

	@hp.setter
	def hp(self, value: int) -> None:
		self._hp = max(0, min(value, self.max_hp))
		if self._hp == 0:
			self.die()

	@property
	def power(self) -> int:
		return self.base_power

	def die(self) -> None:
		if self.engine.player is self.parent:
			death_message = "You died!"
			death_message_color = color.player_die
			self.engine.message_log.messages.clear()
			if hasattr(self.engine, '_current_step_messages'):
				self.engine._current_step_messages.clear()
		else:
			death_message = f"{self.parent.name} is dead!"
			death_message_color = color.enemy_die
			if self.parent.gamemap:
				self.parent.gamemap.entities.remove(self.parent)
        
		self.parent.char = "%"
		self.parent.color = (191, 0, 0)
		self.parent.blocks_movement = False
		self.parent.ai = None
		self.parent.name = f"remains of {self.parent.name}"
		self.parent.render_order = RenderOrder.CORPSE

		self.engine.message_log.add_message(death_message, death_message_color)

	def heal(self, amount: int) -> int:
		if self.hp == self.max_hp:
			return 0
		new_hp_value = self.hp + amount
		if new_hp_value > self.max_hp:
			new_hp_value = self.max_hp
		amount_recovered = new_hp_value - self.hp
		self.hp = new_hp_value
		return amount_recovered

	def take_damage(self, amount: int) -> None:
		self.hp -= amount

	def apply_dungeon_level_scaling(self, dungeon_level: int) -> None:
		if dungeon_level <= 1:
			return
		bonus_hp = (dungeon_level - 1) * 15
		old_max_hp = self.max_hp
		self.max_hp = 100 + bonus_hp
		if old_max_hp < self.max_hp:
			hp_increase = self.max_hp - old_max_hp
			self.hp += hp_increase
			self.engine.message_log.add_message(
				f"adapts to the dungeon's depth! Max health increased by {hp_increase}!",
				color.health_recovered
			)

