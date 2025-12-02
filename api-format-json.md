# API JSON Format Documentation

This document outlines the JSON request and response formats for the Game API.

## Endpoints

### 1. Root / Meta (`GET /`)

Returns metadata about the running game server.

**Response JSON:**

```json
{
  "message": "Roguelike Game API - Pygame Renderer",
  "status": "running" | "waiting_for_game",
  "renderer": "pygame",
  "tile_size": 16
}
```

**Key Descriptions:**
*   `message`: Server identification string.
*   `status`: Current server state. `"running"` if a game is active, `"waiting_for_game"` otherwise.
*   `renderer`: The rendering backend in use (e.g., `"pygame"`).
*   `tile_size`: The current tile size in pixels (e.g., 8 or 16).

---

### 2. Get Game State (`GET /game-state`)

Retrieves the current snapshot of the game state without performing any action.

**Response JSON (`GameStateResponse`):**

```json
{
  "dungeon_level": 1,
  "current_level_step_count": 5,
  "message_log": [
    "You move east.",
    "The ghost attacks you!"
  ],
  "player_standing_on": "floor",
  "player_health": 25,
  "health_potion_count": 1,
  "player_position": [12, 15],
  "stairs": [25, 30] | null,
  "is_done": false,
  "end_reason": null,
  "legal_actions": ["w", "a", "s", "d", "space", "g", "i", ".", "esc", "q"]
}
```

**Key Descriptions:**
*   (Same as `Start Game` response)
*   Returns 400 Bad Request if no game is active.

---

### 3. Start Game (`POST /start-game`)

Initializes a new game session.

**Request JSON:**

```json
{
  "mode": "procedural" | "custom" | "string",
  "custom_map": "<string representation of map>" | null,
  "max_rooms": 30,
  "room_min_size": 4,
  "room_max_size": 6,
  "map_width": 30,
  "map_height": 30,
  "fov_mode": "partial" | "all",
  "fov_radius": 8
}
```

**Key Descriptions:**
*   `mode`: Game generation mode (`"procedural"`, `"custom"`, or `"string"`).
*   `custom_map`: Raw string map data (required if `mode="string"`).
*   `max_rooms`: Maximum number of rooms to generate (procedural only).
*   `room_min_size`: Minimum size of a room (procedural only).
*   `room_max_size`: Maximum size of a room (procedural only).
*   `map_width`: Width of the generated map in tiles (procedural only). Default 30.
*   `map_height`: Height of the generated map in tiles (procedural only). Default 30.
*   `fov_mode`: Field of View type (`"partial"` for limited visibility, `"all"` for full map).
*   `fov_radius`: Radius of vision in tiles (used with `fov_mode="partial"`).

**Logic Constraints:**
*   `mode`: Must be one of `"procedural"`, `"custom"`, or `"string"`.
*   `custom_map`: Required if `mode` is `"string"`.
*   `map_width` / `map_height`: Used for procedural generation. Recommended max: 80x40.

**Response JSON (`GameStateResponse`):**

```json
{
  "dungeon_level": 1,
  "current_level_step_count": 0,
  "message_log": [
    "Hello and welcome, adventurer, to yet another dungeon!",
    "<...>"
  ],
  "player_standing_on": "floor",
  "player_health": 30,
  "health_potion_count": 2,
  "player_position": [10, 15],
  "stairs": [25, 30] | null,
  "is_done": false,
  "end_reason": null | "victory" | "death",
  "legal_actions": ["w", "a", "s", "d", "space", "g", "i", ".", "esc", "q"]
}
```

**Key Descriptions:**
*   `dungeon_level`: Current floor number (starts at 1).
*   `current_level_step_count`: Number of turns taken on the current floor.
*   `message_log`: List of recent game messages (e.g., combat logs).
*   `player_standing_on`: Type of tile the player is currently on (e.g., `"floor"`, `"down_stairs"`).
*   `player_health`: Current Health Points (HP) of the player.
*   `health_potion_count`: Number of health potions in inventory.
*   `player_position`: Player's coordinates `[x, y]`.
*   `stairs`: Coordinates `[x, y]` of the stairs down (if visible/known), else `null`.
*   `is_done`: `true` if the game has ended (win or loss).
*   `end_reason`: Reason for game end (`"victory"`, `"death"`, or `null`).
*   `legal_actions`: List of valid action strings for the next turn.

**Error Response (400 Bad Request):**

```json
{
  "detail": "Mode must be 'custom', 'procedural', or 'string'"
}
```

---

### 4. Perform Action (`POST /perform-action`)

Executes a player action in the game.

**Request JSON:**

```json
{
  "action": "w" | "a" | "s" | "d" | "up" | "down" | "left" | "right" | "space" | "g" | "i" | "." | "esc" | "q"
}
```

**Key Descriptions:**
*   `action`: The command string to execute (e.g., `"w"` for up, `"g"` for pickup).

**Logic Constraints:**
*   `action`: Case-insensitive. Must be one of the valid actions listed above.
    *   Movement: `"w"`, `"a"`, `"s"`, `"d"`, `"up"`, `"down"`, `"left"`, `"right"`
    *   Wait: `"."`
    *   Pickup Item: `"g"`
    *   Use Item: `"i"`
    *   Take Stairs: `"space"`
    *   Quit/Menu: `"esc"`, `"q"`

**Response JSON:**

```json
{
  "action_executed": "w",
  "state_changes": {
    "dungeon_level": 1,
    "current_level_step_count": 1,
    "message_log": [
      "You move north.",
      "<...>"
    ],
    "player_standing_on": "floor",
    "player_health": 30,
    "health_potion_count": 2,
    "player_position": [10, 14],
    "stairs": [25, 30] | null,
    "is_done": false,
    "end_reason": null,
    "legal_actions": ["w", "a", "s", "d", "space", "g", "i", ".", "esc", "q"]
  }
}
```

**Key Descriptions:**
*   `action_executed`: The action string that was actually processed.
*   `state_changes`: The updated `GameStateResponse` object reflecting the new state.

**Error Response (400 Bad Request):**

```json
{
  "detail": "Invalid action: x"
}
```

```json
{
  "detail": "No active game session"
}
```

---

### 5. Get Game Screenshot (`GET /game-screenshot`)

Retrieves a PNG screenshot of the current game view.

**Response:**
*   **Content-Type**: `image/png`
*   **Body**: Binary PNG data.

**Response Headers:**
*   `X-Tile-Size`: Size of a single tile in pixels (e.g., "16").
*   `X-Total-Width-Tiles`: Total width of the game window in tiles (e.g., "80").
*   `X-Total-Height-Tiles`: Total height of the game window in tiles (e.g., "45").
*   `X-Map-Width-Tiles`: Width of the actual game map in tiles.
*   `X-Map-Height-Tiles`: Height of the actual game map in tiles.
*   `X-Total-Width-Pixels`: Total width of the image in pixels.
*   `X-Total-Height-Pixels`: Total height of the image in pixels.
*   `X-Map-Width-Pixels`: Width of the map area in pixels.
*   `X-Map-Height-Pixels`: Height of the map area in pixels.

**Error Response (400 Bad Request):**
```json
{
  "detail": "No active game or failed to capture screenshot"
}
```
