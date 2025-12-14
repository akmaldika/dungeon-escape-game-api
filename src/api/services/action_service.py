from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.api.state import ThreadSafeGameState

logger = logging.getLogger(__name__)


class GameActionService:
    """Service for executing game actions and waiting for state updates."""

    def __init__(self, game_state: ThreadSafeGameState):
        self.game_state = game_state

    def queue_and_wait(
        self, action_key: str, timeout: float = 10.0
    ) -> dict[str, Any] | None:
        """
        Queue an action and wait for the game state to update.

        Args:
            action_key: The action string to queue (e.g., 'w', 'restart_procedural|...').
            timeout: Maximum time to wait for a state change in seconds.

        Returns:
            The new game state snapshot, or None if the game is not active or timed out.
        """
        # Capture current state for comparison
        prev_state = self.game_state.get_state_snapshot()
        prev_step = prev_state.get("current_level_step_count") if prev_state else None
        prev_level = prev_state.get("dungeon_level") if prev_state else None

        # Queue the action
        self.game_state.queue_action(action_key)

        # Wait for state change
        deadline = time.monotonic() + timeout
        new_state = None

        while time.monotonic() < deadline:
            new_state = self.game_state.get_state_snapshot()

            # If game wasn't running and now is (e.g., after start_game)
            if not prev_state and new_state:
                return new_state

            # If game was running and we have a new state
            if new_state:
                current_step = new_state.get("current_level_step_count")
                current_level = new_state.get("dungeon_level")

                # Check for meaningful change
                if current_step != prev_step or current_level != prev_level:
                    return new_state

            time.sleep(0.01)

        return new_state or prev_state
