from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

import numpy as np  # type: ignore
import tcod

if TYPE_CHECKING:
    from src.entities import Actor

class PathfindingService:
    """Service for calculating paths for entities."""

    @staticmethod
    def get_path_to(entity: Actor, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """
        Compute and return a path to the destination (x, y).
        
        If no valid path is found, returns an empty list.
        """
        if not entity.gamemap:
            return []

        cost = np.array(entity.gamemap.tiles["walkable"], dtype=np.int8)

        for e in entity.gamemap.entities:
            # Check that an entity blocks movement and the cost isn't zero (blocking)
            if getattr(e, 'blocks_movement', False) and cost[e.x, e.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[e.x, e.y] += 10

        # Create a graph from the cost array and pass that to a new Pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((entity.x, entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]]
        return [(index[0], index[1]) for index in path]
