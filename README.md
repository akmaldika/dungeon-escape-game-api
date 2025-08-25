# Dungeon Escape Game API

A turn-based roguelike dungeon crawler game with dual control modes: traditional keyboard input and REST API for AI agents. Built with Python using pygame for rendering and FastAPI for the web API.

## Features

- **Dual Control Modes**: Play with keyboard or control via REST API
- **AI-Friendly**: Clean JSON responses and pixel-perfect screenshots for AI model training
- **Custom Maps**: Load custom dungeon layouts from string format
- **Progressive Difficulty**: Dungeon-level-based scaling system
- **Real-time Screenshots**: Get game state as PNG images via API
- **Clean Game State**: Structured JSON responses with complete game information

## Game Mechanics

- **Turn-based Combat**: Strategic combat with health and damage systems
- **Field of View**: Dynamic lighting and vision mechanics using tcod algorithms
- **Level Progression**: Health scaling based on dungeon level (+15 HP per level beyond 1)
- **Inventory System**: Direct health potion usage with 'i' key
- **Message System**: Clean death handling and step-based message tracking

## Installation

### Prerequisites

- Python 3.8 or higher
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

3. **Create environment file** (optional):
   ```bash
   # Create .env file for configuration
   echo "API_HOST=localhost" > .env
   echo "API_PORT=8000" > .env
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

- **Movement**: Arrow keys or WASD
- **Wait**: Period (.) key - skip a turn
- **Inventory**: 'i' key - use health potion
- **Menu Navigation**: ESC key - return to main menu
- **Confirm**: Enter key

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Get Game Screenshot
```http
GET /game-screenshot
```

**Response**: PNG image with headers containing game dimensions

**Headers**:
- `Game-Width`: Game area width in pixels
- `Game-Height`: Game area height in pixels  
- `Total-Width`: Total window width in pixels
- `Total-Height`: Total window height in pixels
- `Tile-Size`: Individual tile size in pixels (16x16)

#### 2. Get Game State
```http
GET /game-state
```

**Response**:
```json
{
  "current_state": "InGameEventHandler",
  "player": {
    "x": 25,
    "y": 25, 
    "hp": 30,
    "max_hp": 30,
    "name": "Player"
  },
  "dungeon_level": 1,
  "step_count": 42,
  "message_log": [
    "Hello and welcome, adventurer, to yet another dungeon!",
    "You descend the staircase."
  ],
  "current_step_messages": [],
  "entities": [
    {
      "x": 30,
      "y": 25,
      "name": "Ghost",
      "hp": 10,
      "max_hp": 10
    }
  ],
  "items": [
    {
      "x": 35,
      "y": 30,
      "name": "Health Potion"
    }
  ],
  "stairs_position": {"x": 40, "y": 35}
}
```

#### 3. Perform Action
```http
POST /action
Content-Type: application/json

{
  "action": "move",
  "direction": [0, -1]
}
```

**Available Actions**:

**Movement**:
```json
{"action": "move", "direction": [0, -1]}  // North
{"action": "move", "direction": [0, 1]}   // South  
{"action": "move", "direction": [-1, 0]}  // West
{"action": "move", "direction": [1, 0]}   // East
```

**Combat**:
```json
{"action": "bump", "direction": [0, -1]}  // Attack enemy to the north
```

**Other Actions**:
```json
{"action": "wait"}                        // Skip turn
{"action": "use_inventory"}              // Use health potion
{"action": "take_stairs"}                // Descend to next level
{"action": "pickup"}                     // Pick up item at current position
```

**Response**:
```json
{
  "success": true,
  "message": "Action performed successfully",
  "new_state": "InGameEventHandler"
}
```

#### 4. Start New Game
```http
POST /new-game
```

**Response**:
```json
{
  "success": true,
  "message": "New game started"
}
```

#### 5. Load Custom Map
```http
POST /load-custom-map
Content-Type: application/json

{
  "map_string": "##########\n#@.......#\n#.......h#\n#...O....#\n#........#\n#.......>#\n##########"
}
```

**Map Legend**:
- `#`: Wall
- `.`: Floor
- `@`: Player starting position
- `>`: Stairs to next level
- `O`: Ghost enemy
- `T`: Crab enemy  
- `h`: Health potion

**Response**:
```json
{
  "success": true,
  "message": "Custom map loaded successfully"
}
```

## Game States

The game operates in different states:

- **MainMenuEventHandler**: Main menu selection
- **InGameEventHandler**: Active gameplay
- **GameOverEventHandler**: Player died
- **GameDoneEventHandler**: Game completed (reached final level)

## Development

### Project Structure

```
game/
├── main.py                 # Main entry point and API server
├── pygame_renderer.py      # Pygame rendering system  
├── engine.py              # Game engine and logic
├── game_map.py            # Map generation and management
├── entity.py              # Base entity classes
├── entity_factories.py    # Predefined entity templates
├── custom_map_loader.py   # Custom map parsing
├── input_handlers.py      # Keyboard and game state handlers
├── actions.py             # Game action implementations
├── components/            # ECS components
│   ├── fighter.py         # Combat and health
│   ├── ai.py             # Enemy AI behavior
│   ├── inventory.py       # Inventory management
│   └── level.py          # Level tracking
├── assets/               # Game sprites and graphics
└── test/                # Test files
```

### Testing

Run the test suite:
```bash
# Test API endpoints
python test/test_api_client.py

# Quick gameplay test
python test/quick_test.py
```

### Custom Map Format

Create custom maps using a simple string format:

```python
custom_map = """##########
#@.......#
#.......h#
#...O....#
#........#
#.......>#
##########"""
```

## API Usage Examples

### Python Client Example

```python
import requests
import json

# Start new game
response = requests.post('http://localhost:8000/new-game')
print(response.json())

# Get current game state  
response = requests.get('http://localhost:8000/game-state')
game_state = response.json()
print(f"Player at: ({game_state['player']['x']}, {game_state['player']['y']})")

# Move player north
action = {"action": "move", "direction": [0, -1]}
response = requests.post('http://localhost:8000/action', json=action)
print(response.json())

# Get screenshot
response = requests.get('http://localhost:8000/game-screenshot')
with open('game_screenshot.png', 'wb') as f:
    f.write(response.content)
print(f"Game dimensions: {response.headers['Game-Width']}x{response.headers['Game-Height']}")
```

### AI Agent Integration

The API is designed for AI agents with:
- Clean JSON responses without terminal escape codes
- Pixel-perfect screenshots for computer vision
- Comprehensive game state information
- Simple action format for reinforcement learning

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `.env` file or kill the existing process
2. **Module not found**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Pygame display issues**: Make sure you have display capabilities if running on a server

### Debug Mode

Add debug logging by setting environment variable:
```bash
export DEBUG=1
python main.py
```

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
