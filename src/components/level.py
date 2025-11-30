from __future__ import annotations

from typing import TYPE_CHECKING
from src.components.base_component import BaseComponent
if TYPE_CHECKING:
	from src.core.entity import Actor


class Level(BaseComponent["Actor"]):

	def __init__(self):
		"""Simplified level component - no XP system, just dungeon-level-based scaling."""
		pass

