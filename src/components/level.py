from __future__ import annotations

from typing import TYPE_CHECKING
from src.components.base_component import BaseComponent

if TYPE_CHECKING:
    from src.entities.entity import Actor


class Level(BaseComponent["Actor"]):
    """
    Component for managing entity levels and experience.
    Currently simplified to support dungeon-level scaling only.
    """

    def __init__(self) -> None:
        """Simplified level component - no XP system, just dungeon-level-based scaling."""
        pass
