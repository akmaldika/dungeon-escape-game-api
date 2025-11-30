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
    """
    The main game engine that manages the game loop, rendering, and state.
    """
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor, fov_mode: str = "partial", fov_radius: int = 8):
        self.message_log = MessageLog(self)
        self.player = player
        self.step_counter = 0
        self.is_using_custom_map = False
        self.game_done = False
        self._current_step_messages: list[dict[str, str | int]] = []
        self.fov_mode = fov_mode  # "partial" or "all"
        self.fov_radius = fov_radius  # Only used if fov_mode="partial"
        self.last_console: Console | None = None

    def start_new_step(self) -> None:
        """Called at the beginning of each new step to reset message tracking."""
        self._current_step_messages = []
        self.step_counter += 1

    def add_step_message(self, message: str) -> None:
        """Add a message that occurred in the current step with consecutive counting."""
        if self._current_step_messages and self._current_step_messages[-1]['text'] == message:
            # We know count is int, but type checker might need help or we just ignore
            self._current_step_messages[-1]['count'] += 1  # type: ignore
        else:
            self._current_step_messages.append({'text': message, 'count': 1})

    def handle_enemy_turns(self) -> None:
        """Handle the turns of all enemies (non-player actors)."""
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the player's point of view."""
        if self.fov_mode == "all":
            # All tiles visible (no fog of war)
            self.game_map.visible[:] = True
        else:
            # Partial visibility with configurable radius
            self.game_map.visible[:] = compute_fov(
                self.game_map.tiles["transparent"],
                (self.player.x, self.player.y),
                radius=self.fov_radius,
            )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        """Render the game map and interface to the console."""
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
        """Get the current dungeon level."""
        return getattr(self.game_world, 'current_floor', 1)

    def get_player_tile_type(self) -> str:
        """Get the description of the tile the player is standing on."""
        if self.game_done:
            return "-"
        x, y = self.player.x, self.player.y
        
        # Check for stairs/ladder
        if hasattr(self.game_map, 'downstairs_location') and self.game_map.downstairs_location is not None:
            dx = abs(x - self.game_map.downstairs_location[0])
            dy = abs(y - self.game_map.downstairs_location[1])
            if (dx == 0 and dy == 0) or (dx + dy == 1):
                return "ladder/stairs"
        
        # Check for items
        for item in self.game_map.items:
            if item.x == x and item.y == y:
                return f"item({item.name}) (press 'g' to pick up)"
        
        return "floor"
