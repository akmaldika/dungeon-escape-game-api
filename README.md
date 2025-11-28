## Endpoints

### 1. GET /game-state

Response (shape):

```json
{
  "dungeon_level": 1,
  "current_level_step_count": 0,
  "message_log": [
    "You descend the staircase.",
    "You feel refreshed! Restored 5 health."
  ],
  "player_standing_on": "floor",
  "player_health": 10,
  "health_potion_count": 2,
  "is_done": false,
  "end_reason": null,
  "legal_actions": [
    "w","up","a","left","s","down","d","right",".","g","i","space"
  ]
}
```

Field reference:
- `dungeon_level` (int): Current dungeon floor, 1-based.
- `current_level_step_count` (int): Number of turns taken on the current floor. Resets when you move to a new floor.
- `message_log` (string[]): Messages for the current step; consecutive duplicates are compacted as “(N times)”.
- `player_standing_on` (string): Description of the tile under the player. Values include:
  - "floor"
  - "item(Health Potion) (press 'g' to pick up)"
  - "ladder/stairs"
  - "-" when game already done
- `player_health` (int): Player HP at time of query.
- `health_potion_count` (int): Count of health potions in inventory.
- `is_done` (bool): Episode ended flag.
- `end_reason` ("victory" | "death" | null): Why the episode ended.
  - "victory": Player reached stairs on custom/static map and pressed SPACE.
  - "death": Player HP reached 0 on any map.
- `legal_actions` (string[]): Allowed inputs now. Contains movement (WASD + arrows) when the target tile is walkable or has an enemy, `g` only on items, `i` if any potion in inventory, `space` only on stairs.

Errors:
- 400: No active game session (e.g., game not started or not in a playable state).

### 2. GET /observation

Single-call observation that pairs pixels with structured state. Returns JSON:

```json
{
  "step_id": 3,
  "dungeon_level": 1,
  "is_done": false,
  "end_reason": null,
  "screenshot_png_base64": "...",
  "player": {"x": 10, "y": 5, "hp": 7, "power": 2},
  "enemies": [{"name": "Ghost", "x": 12, "y": 5, "hp": 10, "power": 2}],
  "items": [{"name": "Health Potion", "x": 9, "y": 5}],
  "stairs": [15, 8],
  "visible_mask": [[true, false, ...], ...],
  "legal_actions": ["w","up", ".", "g"]
}
```

Field reference:
- `step_id` (int): Turn counter for current floor (same basis as `current_level_step_count`).
- `dungeon_level` (int): Current dungeon floor, 1-based.
- `is_done` / `end_reason`: Same semantics as `/game-state`.
- `screenshot_png_base64` (string): Base64-encoded PNG of the full frame (exact pixels).
- `player` (object): `{ x, y, hp, power }` for the player.
- `enemies` (array): Visible enemies only. Each `{ name, x, y, hp, power }`.
- `items` (array): Visible items only. Each `{ name, x, y }`.
- `stairs` ([x, y] | null): Stairs if inside FOV.
- `visible_mask` (bool[H][W]): Row-major mask (height x width). `true` where tile is inside current FOV. entities/items/stairs only appear if their tile is `true`.
- `legal_actions` (string[]): Same filtering rules as in `/game-state`.

Errors:
- 400: No active game session (e.g., game not started). Works after victory/death screens as well.

### 3. GET /game-screenshot

Returns a screenshot in either base64 JSON or raw bytes.

- Query param: `fmt=b64|bytes` (default: `b64`)
  - `b64` response:
    ```json
    {
      "screenshot_png_base64": "...",
      "tile_size": 16,
      "total_width_tiles": 60,
      "total_height_tiles": 40,
      "map_width_tiles": 30,
      "map_height_tiles": 30,
      "total_width_pixels": 960,
      "total_height_pixels": 640,
      "map_width_pixels": 480,
      "map_height_pixels": 480
    }
    ```
  - `bytes` response: `image/png` with the same dimension metadata in headers.

Errors:
- 400: No active game or failed to capture screenshot.

### 4. POST /start-game

Body:
```json
{ "mode": "procedural" | "custom" | "string", "custom_map": "..." }
```

Returns the same shape as GET `/game-state`. When `mode=string`, `custom_map` (ASCII map) is required.

Modes and semantics:
- `procedural`:
  - Generates a random dungeon.
  - SPACE on stairs descends to the next floor (does NOT end the episode).
  - `is_done` becomes `true` only if the player dies (`end_reason = "death").
- `custom`:
  - Loads a predefined map file (`custom_map.txt`).
  - Pressing SPACE on stairs ends the episode with victory (`end_reason = "victory").
- `string`:
  - Loads an inline ASCII map from `custom_map`.
  - Same termination as `custom` (SPACE on stairs => victory).

FOV configuration (optional fields supported in the request body):
- `fov_mode`: `"partial"` (default) or `"all"` — when `all` everything is visible; when `partial` visibility is limited by `fov_radius`.
- `fov_radius`: integer radius (only used when `fov_mode` is `partial`).

ASCII map legend (for `mode=string`):
- `#` = wall (blocked)
- `.` = floor (walkable)
- `@` = player start (recommended one occurrence)
- `>` = stairs/exit (required for a solvable map)
- `O` = ghost (enemy)
- `T` = Red Ghost (enemy)
- `h` = health potion (item)

Constraints and notes:
- All rows should have equal length (rectangular map).
- Provide at least one `@` (player) and one `>` (stairs).

Errors:
- 400: Invalid mode (must be `procedural`, `custom`, or `string`).
- 400: `custom_map` missing when `mode="string"`.
- 500: Failed to start game (if initialization didn’t complete in time).

### 5. POST /perform-action

Body:
```json
{ "action": "w|a|s|d|up|down|left|right|g|i|space|.|esc|q" }
```

Returns:
```json
{ "action_executed": "w", "state_changes": { /* same as /game-state */ } }
```

The API waits for the step to advance (or level to change) before returning, ensuring turn-based sync for agents.

Errors:
- 400: Invalid action key.
- 400: No active game session.
- 400: No active game session.

- The endpoint returns after the turn is applied or a short timeout if no state change is detected.
Notes:
- The endpoint returns after the turn is applied or a short timeout if no state change is detected.
- UI keys like `esc` and `q` are accepted; when the game is in a Game Over or Game Done state they will return to the main menu.
- The endpoint returns after the turn is applied or a short timeout if no state change is detected.

# Dungeon Escape Game API

A turn-based roguelike dungeon crawler game with dual control modes: traditional keyboard input and REST API for AI agents. Built with Python using pygame for rendering and FastAPI for the web API.

## Installation

### Prerequisites

- Python 3.12 or higher
- pip package manager

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/dungeon-escape-game-api.git
   cd dungeon-escape-game-api
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```


## Running the Game

### Start the Game Server


```bash
python main.py
```

This will:
- Launch the pygame window for keyboard play
- Start the FastAPI server on `http://localhost:8000`
- Display the main menu with options to start or load custom maps

### Game Controls (Keyboard Mode)

- Movement: Arrow keys or WASD
- Wait: Period (.) key
- Inventory: i (use health potion)
- Pickup: g
- Use stairs: Space

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /
```
Returns basic server info and tile size.

#### 2. Get Game State
```http
GET /game-state
```

**Response**:
```json
{
  "dungeon_level": 1,
  "current_level_step_count": 42,
  "message_log": ["You descend the staircase."],
  "player_standing_on": "floor",
  "player_health": 30,
  "health_potion_count": 1
}
```

#### 3. Perform Action
```http
POST /perform-action
POST /action  # alias
Content-Type: application/json

{ "action": "w" }        # also: a,s,d, up,down,left,right
{ "action": "." }        # wait
{ "action": "g" }        # pickup
{ "action": "i" }        # use health potion
{ "action": "space" }    # take stairs
```

#### 4. Start New Game
```http
POST /start-game
Content-Type: application/json
```
Body options:
- Procedural (random): `{ "mode": "procedural" }`
- Custom predefined map file: `{ "mode": "custom" }`
- Inline string map: `{ "mode": "string", "custom_map": "########\n#@..>..#\n########" }`

Legend: `#` wall, `.` floor, `@` player, `>` stairs, `O` ghost, `T` red ghost, `h` health potion.

Response matches GET /game-state.

#### 5. Get Game Screenshot
```http
GET /game-screenshot
```
Returns PNG bytes. Headers include dimensions:
- `X-Tile-Size`
- `X-Total-Width-Tiles`, `X-Total-Height-Tiles`
- `X-Map-Width-Tiles`, `X-Map-Height-Tiles`
- `X-Total-Width-Pixels`, `X-Total-Height-Pixels`
- `X-Map-Width-Pixels`, `X-Map-Height-Pixels`

#### 6. Get Technical Game Information
```http
GET /game-info
```
Returns structured info (type, stats, capabilities, interactions, image_url, tile_size).

#### 7. Get Single Sprite/Tile Image
```http
GET /sprite/{name}.png
```
Examples: `/sprite/player.png`, `/sprite/wall.png`, `/sprite/ladder.png`.

## API Usage Examples (curl)

Here are comprehensive curl examples for all API endpoints:

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/"
```

### 2. Get Current Game State
```bash
curl -X GET "http://localhost:8000/game-state"
```

### 3. Get Technical Game Information
```bash
curl -X GET "http://localhost:8000/game-info"
```
Returns structured technical info:
```json
{
  "Ghost": {
    "type": "enemy",
    "stats": {"health": 10, "power": 2},
    "capabilities": ["hostile", "moves", "attacks_on_bump"],
    "interactions": [{"bumpable": ["w","a","s","d","up","down","left","right"]}],
    "image_url": "/sprite/ghost.png",
    "tile_size": 16
  }
}
```

### 4. Get Game Screenshot
```bash
# Save screenshot to file
curl -X GET "http://localhost:8000/game-screenshot" --output screenshot.png

# View response headers (includes dimension info)
curl -X GET "http://localhost:8000/game-screenshot" -I
```

### 5. Start New Game

**Procedural Map (Random Generation):**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "procedural"}'
```

**Procedural with FOV (partial):**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "procedural", "fov_mode": "partial", "fov_radius": 8}'
```

**Procedural with FOV (all visible):**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "procedural", "fov_mode": "all"}'
```

**Custom Predefined Map:**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "custom"}'
```

**Custom String Map:**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "string", "custom_map": "################\n#.............>#\n#####.##########\n    #.#\n    #.#\n    #.#\n#####.##\n#@.....#\n########"}'
```

**String map with FOV radius 6:**
```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "string", "custom_map": "##########\n#@.......#\n#.......h#\n#...O....#\n#........#\n#.......>#\n##########", "fov_mode": "partial", "fov_radius": 6}'
```

```bash
curl -X POST "http://localhost:8000/start-game" -H "Content-Type: application/json" -d '{"mode": "string", "custom_map": "##############\n#@.....#.....#\n#..#......#..#\n#..#......#..#\n#..#...#.....#\n#......#.....#\n#.....>#.....#\n#............#\n#..#...#.....#\n##############", "fov_mode":"all"}'
```




### 6. Perform Actions

**Movement:**
```bash
# Move North
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "w"}'

# Move South
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "s"}'

# Move West
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "a"}'

# Move East
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "d"}'

# Arrow keys also work
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "up"}'
```

**Game Actions:**
```bash
# Use Health Potion
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "i"}'

# Pick up Item
curl -X POST "http://localhost:8000/perform-action" -H "Content-Type: application/json" -d '{"action": "g"}'

# Use Stairs (go to next level)
curl -X POST "http://localhost:8000/perform-action" \
  -H "Content-Type: application/json" \
  -d '{"action": "space"}'

# Wait/Skip Turn
curl -X POST "http://localhost:8000/perform-action" \
  -H "Content-Type: application/json" \
  -d '{"action": "."}'
```

### 7. Example Game Session
```bash
# Start a new procedural game
curl -X POST "http://localhost:8000/start-game" \
  -H "Content-Type: application/json" \
  -d '{"mode": "procedural"}' | jq .

# Move around
curl -X POST "http://localhost:8000/perform-action" \
  -H "Content-Type: application/json" \
  -d '{"action": "w"}' | jq .

curl -X POST "http://localhost:8000/perform-action" \
  -H "Content-Type: application/json" \
  -d '{"action": "d"}' | jq .

# Check current state
curl -X GET "http://localhost:8000/game-state" | jq .

# Take a screenshot
curl -X GET "http://localhost:8000/game-screenshot" --output current_state.png
```

### 8. Custom Map Example
```bash
# Load a specific custom map layout
curl -X POST "http://localhost:8000/start-game" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "string",
    "custom_map": "############\n#@........h#\n#..........#\n#....O.....#\n#..........#\n#....T.....#\n#..........#\n#.........>#\n############"
  }' | jq .
```

### 9. Monitoring Script
```bash
#!/bin/bash
# monitor_game.sh - Continuously monitor game state
while true; do
  echo "=== Game State ==="
  curl -s "http://localhost:8000/game-state" | jq .
  echo ""
  sleep 2
done
```

**Note:** Examples using `| jq .` require the `jq` command-line JSON processor for pretty-printing. Install with `apt-get install jq` (Ubuntu) or `brew install jq` (macOS).

## Game States

The game operates in different states:

- **MainMenuEventHandler**: Main menu selection
- **InGameEventHandler**: Active gameplay
- **GameOverEventHandler**: Player died
- **GameDoneEventHandler**: Game completed (reached final level)

## Troubleshooting

### Common Issues

1. **Port already in use**: Run on a different port using uvicorn CLI args
2. **Module not found**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Pygame display issues**: Make sure you have display capabilities if running on a server

### Debug Mode

Use uvicorn log level flags when running directly.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Built on the tcod tutorial framework
- Uses pygame for cross-platform rendering
- FastAPI for modern web API capabilities