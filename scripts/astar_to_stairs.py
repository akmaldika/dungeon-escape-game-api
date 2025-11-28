#!/usr/bin/env python3
"""
A simple A* pathfinder for the dungeon maps in this project.

Usage:
    python scripts/astar_to_stairs.py <map_file> [--show-path]

Output: number of steps required to reach stairs '>' from player '@' plus 1 (for pressing 'space').

Notes:
- '#' are walls and cannot be traversed.
- ' ' (space) is void and cannot be traversed.
- All other characters are treated as walkable, including items and enemies (e.g. 'O', 'T', 'h').
"""

from __future__ import annotations

import argparse
import heapq
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable

Point = Tuple[int, int]

WALL_CHARS = {"#"}
VOID_CHARS = {" "}


def load_map(file: Path) -> List[List[str]]:
    text = file.read_text(encoding="utf-8")
    lines = text.splitlines()
    width = max(len(line) for line in lines) if lines else 0
    grid: List[List[str]] = []
    for line in lines:
        row = list(line.ljust(width))
        grid.append(row)
    return grid


def find_player_and_stairs(grid: List[List[str]]) -> Tuple[Point, Point]:
    player: Optional[Point] = None
    stairs: Optional[Point] = None
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "@":
                player = (x, y)
            elif ch == ">":
                stairs = (x, y)
    if player is None:
        raise SystemExit("Player '@' not found in map")
    if stairs is None:
        raise SystemExit("Stairs '>' not found in map")
    return player, stairs


def in_bounds(grid: List[List[str]], p: Point) -> bool:
    x, y = p
    return 0 <= y < len(grid) and 0 <= x < len(grid[0])


def is_passable(grid: List[List[str]], p: Point) -> bool:
    x, y = p
    ch = grid[y][x]
    if ch in WALL_CHARS:
        return False
    if ch in VOID_CHARS:
        return False
    return True


def neighbors(grid: List[List[str]], p: Point) -> Iterable[Point]:
    x, y = p
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        np = (x + dx, y + dy)
        if in_bounds(grid, np) and is_passable(grid, np):
            yield np


def heuristic(a: Point, b: Point) -> int:
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from: Dict[Point, Point], current: Point) -> List[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def a_star_search(grid: List[List[str]], start: Point, goal: Point) -> Optional[List[Point]]:
    if start == goal:
        return [start]

    open_heap: List[Tuple[int, int, Point]] = []
    heapq.heappush(open_heap, (0, 0, start))

    came_from: Dict[Point, Point] = {}
    g_score: Dict[Point, int] = {start: 0}

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in neighbors(grid, current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f, tentative_g, neighbor))

    return None


def pretty_print_with_path(grid: List[List[str]], path: List[Point]) -> None:
    grid_copy = [row[:] for row in grid]
    for (x, y) in path:
        if grid_copy[y][x] == "@":
            continue
        if grid_copy[y][x] == ">":
            continue
        grid_copy[y][x] = "*"
    for row in grid_copy:
        print("".join(row))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("map_file", type=Path, help="Path to map file")
    parser.add_argument("--show-path", action="store_true", help="Print the path overlay on the map")
    args = parser.parse_args()

    grid = load_map(args.map_file)

    # For pathfinding treat enemies and items as walkable (like floor)
    # But we must keep original characters to display path.

    start, goal = find_player_and_stairs(grid)

    print(f"Map size: {len(grid[0])}x{len(grid)}")
    print(f"Start: {start}, Goal: {goal}")

    path = a_star_search(grid, start, goal)
    if path is None:
        print("No path found from @ to >")
        return

    # Steps to reach stairs = number of moves = len(path)-1
    moves = len(path) - 1
    total_steps_with_space = moves + 1

    print(f"Moves to reach stairs: {moves}")
    print(f"Total steps including pressing space: {total_steps_with_space}")

    if args.show_path:
        pretty_print_with_path(grid, path)


if __name__ == "__main__":
    main()
