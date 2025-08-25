from __future__ import annotations

import lzma
import pickle
import os
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from tcod.console import Console
from tcod.map import compute_fov

import exceptions
from message_log import MessageLog

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog(self)
        self.player = player
        self.step_counter = 0
        self.game_id = self.get_next_game_id()
        self.is_using_custom_map = False  # Add this flag
        self.game_done = False  # Flag untuk game done
        self._current_step_messages = []  # Track messages for current step
        self._ensure_log_directory()
        self._clear_current_game_log()  # Add this line


    def get_next_game_id(self) -> int:
        """Get next game ID by checking existing game folders."""
        base_path = "data/logs"
        os.makedirs(base_path, exist_ok=True)
        
        game_folders = [d for d in os.listdir(base_path) if d.startswith("game_") and os.path.isdir(os.path.join(base_path, d))]
        if not game_folders:
            return 1
        
        # Extract game numbers and find the highest
        game_numbers = []
        for folder in game_folders:
            try:
                num = int(folder.replace("game_", ""))
                game_numbers.append(num)
            except ValueError:
                continue
        
        return max(game_numbers) + 1 if game_numbers else 1

    def _ensure_log_directory(self) -> None:
        """Create log directory structure for current game session."""
        self.log_dir = f"./data/logs"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _clear_current_game_log(self) -> None:
        """Clear the current game log file at the start of a new game."""
        filename = "game_state_log.txt"
        filepath = os.path.join(self.log_dir, filename)
        
        # Clear the file by writing empty content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")  # Empty file

    def start_new_step(self) -> None:
        """Called at the beginning of each new step to reset message tracking."""
        self._current_step_messages = []
        self.step_counter += 1

    def add_step_message(self, message: str) -> None:
        """Add a message that occurred in the current step with consecutive counting."""
        
        # Check if the last message is the same (consecutive)
        if self._current_step_messages and self._current_step_messages[-1]['text'] == message:
            self._current_step_messages[-1]['count'] += 1
        else:
            # If it's a different message or first message, add new entry
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
        
        ##
        console_width = console.width
        console_height = console.height

        self.message_log.render(
            console=console,
            x=console_width // 4,  # Example: 1/4 from the left
            y=console_height - 5,  # 5 rows from the bottom
            width=console_width // 2,
            height=5,
        )

    def get_current_level(self) -> int:
        """Get current dungeon level (1-based)."""
        return getattr(self.game_world, 'current_floor', 1)

    def log_game_state(self) -> None:
        """Log current game state to a single file, overwriting each time."""
        if not hasattr(self, 'game_world'):
            return

        current_level = self.game_world.current_floor
        filename = "game_state_log.txt"
        filepath = os.path.join(self.log_dir, filename)

        # Get messages from current step only
        message_log_text = ""
        if hasattr(self, '_current_step_messages') and self._current_step_messages:
            formatted_messages = []
            for msg_data in self._current_step_messages:
                if msg_data['count'] > 1:
                    formatted_messages.append(f"- {msg_data['text']} ({msg_data['count']} times)")
                else:
                    formatted_messages.append(f"- {msg_data['text']}")
            message_log_text = "\n".join(formatted_messages)

        # Special case for game done
        if self.game_done:
            message_log_text = "- Game Done Congratulation (Press 'q' to quit)"

        # Get player tile type
        player_tile = self.get_player_tile_type()
        
        # Get player health
        player_health = f"{self.player.fighter.hp}/{self.player.fighter.max_hp}"

        # Write to first file (overwrite mode)
        content = f"""current level: {current_level}
step: {self.step_counter}
message log:
{message_log_text}

player standing on: {player_tile}
player's health: {player_health}
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def get_player_tile_type(self) -> str:
        """Get the type of tile the player is standing on."""
        # If game is done, return "-" as position is no longer relevant
        if self.game_done:
            return "-"
            
        x, y = self.player.x, self.player.y
        
        # Check if standing on stairs
        if hasattr(self.game_map, 'downstairs_location') and (x, y) == self.game_map.downstairs_location:
            return "ladder/stairs"
        
        # Check if standing on any item
        for item in self.game_map.items:
            if item.x == x and item.y == y:
                return f"item({item.name}) (press 'g' to pick up)"
        
        # Default to floor (since player can only walk on walkable tiles)
        return "floor"
