# Dungeon Escape Game API

A turn-based roguelike dungeon crawler game with dual control modes: a traditional playable window (Pygame) and a REST API for AI agents. Built with Python using **Pygame** for rendering and **FastAPI** for the game server.

## Features

- **Dual Control**: Play manually or control via API.
- **Rendering Modes**:
  - `sprite`: Modern pixel art (8x8 or 16x16).
  - `char`: Classic ASCII roguelike look (White on Black).
  - `char_color`: Colored ASCII on high-contrast backgrounds.
- **Visuals**: FOV system with fog of war (explored areas are dimmed by 50%).
- **Procedural Generation**: Random dungeon layouts.
  - Classic Dungeon (Rectangular rooms + corridors).
  - Cellular Automata (Organic caves).
- **Custom Maps**: Load maps from files or strings.
- **Headless Mode**: Run without a window for fast AI training.

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

Start the game server using `python main.py`. You can configure the rendering mode, tile size, and port via command-line arguments.

### Basic Usage

```bash
# Default (Sprite mode, 8x8 tiles, Port 8000)
python main.py

# Classic ASCII mode
python main.py --render-mode char

# Colored ASCII mode
python main.py --render-mode char_color

# Headless mode (no window, for AI agents)
python main.py --headless
```

### Command Line Arguments

| Argument        | Short | Description                                     | Default  |
| --------------- | ----- | ----------------------------------------------- | -------- |
| `--render-mode` | `-m`  | Rendering style: `sprite`, `char`, `char_color` | `sprite` |
| `--tile-size`   | `-t`  | Tile size in pixels (`8` or `16`)               | `8`      |
| `--port`        | `-p`  | API Server port                                 | `8000`   |
| `--headless`    |       | Run without a visible window                    | `False`  |

### Manual Controls (Window Mode)

- **Movement**: Arrow keys or WASD
- **Wait**: Period (`.`)
- **Inventory**: `i` (use health potion)
- **Pickup**: `g`
- **Use Stairs**: `Space`
- **Quit**: `Esc` or `Q`

## API Documentation

The REST API allows agents to observe the state and perform actions.

**Base URL**: `http://localhost:8000` (or your configured port)

### 1. Health Check

`GET /`
Returns server status and configuration.

```bash
curl http://localhost:8000/
```

**PowerShell:**

```powershell
curl "http://localhost:8000/"
```

### 2. Start Game

`POST /start-game`
Initialize a new session.

**Body Parameters:**

- `mode`: Map generation mode:
  - `"procedural"` (Default Dungeon)
  - `"cellular"` (Cellular Automata/Caves)
  - `"custom"` (load file)
  - `"string"` (raw data)
- `fov_mode`: `"partial"` (default) or `"all"`.
- `fov_radius`: Integer (default 8).
- `map_width`, `map_height`: Dimensions for procedural maps.

**Example (Procedural):**

```bash
curl -X POST "http://localhost:8000/start-game" \
     -H "Content-Type: application/json" \
     -d '{"mode": "procedural", "fov_mode": "partial", "fov_radius": 8}'
```

**PowerShell:**

```powershell
curl `
  -X POST `
  "http://localhost:8000/start-game" `
  -H "Content-Type: application/json" `
  -d '{"mode": "procedural", "fov_mode": "partial", "fov_radius": 8}'
```

**Example (Cellular Automata):**

```bash
curl `
  -X POST `
  "http://localhost:8000/start-game" `
  -H "Content-Type: application/json" `
  -d '{"mode": "cellular", "map_width": 80, "map_height": 40}'
```

**PowerShell:**

```powershell
curl `
  -X POST `
  "http://localhost:8000/start-game" `
  -H "Content-Type: application/json" `
  -d '{"mode": "cellular", "map_width": 80, "map_height": 40}'
```

**Example (Custom String Map):**

```bash
curl -X POST "http://localhost:8000/start-game" \
     -H "Content-Type: application/json" \
     -d '{
       "mode": "string",
       "custom_map": "##########\n#@.......>\n##########"
     }'
```

**PowerShell:**

```powershell
curl `
  -X POST `
  "http://localhost:8000/start-game" `
  -H "Content-Type: application/json" `
  -d @'
{
  "mode": "string",
  "custom_map": "###########\n#@.......>#\n###########"
}
'@
```

### 3. Get State

`GET /game-state`
Returns the current observation (JSON).

```bash
curl http://localhost:8000/game-state
```

**PowerShell:**

```powershell
curl "http://localhost:8000/game-state"
```

**Response includes:**

- `dungeon_level`: Current floor.
- `player_position`, `player_health`.
- `visible_mask`: FOV data.
- `legal_actions`: List of valid moves.
- `message_log`: Recent game events.

### 4. Perform Action

`POST /perform-action`
Send a command to the agent.

**Body:** `{ "action": "<key>" }`

**Valid Actions:**

- Movement: `w`, `a`, `s`, `d`, `up`, `down`, `left`, `right`
- Interact: `g` (pickup), `i` (use potion), `space` (stairs), `.` (wait)

**Example:**

```bash
curl -X POST "http://localhost:8000/perform-action" \
     -H "Content-Type: application/json" \
     -d '{"action": "w"}'
```

**PowerShell:**

```powershell
curl `
  -X POST `
  "http://localhost:8000/perform-action" `
  -H "Content-Type: application/json" `
  -d '{"action": "w"}'
```

### 5. Get Screenshot

`GET /game-screenshot`
Returns a PNG image of the current frame.

```bash
curl http://localhost:8000/game-screenshot --output view.png
```

**PowerShell:**

```powershell
curl "http://localhost:8000/game-screenshot" --output view.png
```

## Monitoring Script

You can use this script to watch the game state in a terminal:

```bash
#!/bin/bash
while true; do
  clear
  echo "=== Game State ==="
  curl -s "http://localhost:8000/game-state" | jq .
  sleep 1
done
```

**PowerShell:**

```powershell
while ($true) {
    Clear-Host
    Write-Host "=== Game State ==="
    curl -s "http://localhost:8000/game-state" | ConvertFrom-Json | ConvertTo-Json -Depth 5
    Start-Sleep -Seconds 1
}
```

_Note: These examples use the standard `curl` command syntax. If `curl` is aliased to `Invoke-WebRequest` in your PowerShell (default), you may need to use `curl.exe` or remove the alias._

## Utility Scripts

We provide several utility scripts in the `scripts/` directory to help developers:

1.  **`clean_log.py`**: Deletes all generated logs in `log/`.
2.  **`astar_to_stairs.py`**: Solves a map file using A\* pathfinding.
3.  **`randomize_effect.py`**: Generates color-varied assets from base sprites.

See [scripts/README.md](scripts/README.md) for full usage instructions.

## Game States

- **MainMenu**: The start screen.
- **InGame**: Active gameplay.
- **GameOver**: Player died.
- **GameDone**: Victory condition met.

## License

This project is open source and available under the [MIT License](LICENSE).
