# Utility Scripts

This directory contains utility scripts for managing logs, processing assets, and analyzing maps.

## Scripts

### 1. `clean_log.py`

Cleans up the `log/` directory by removing all generated log files and subdirectories.

**Usage:**

```bash
python scripts/clean_log.py
```

### 2. `astar_to_stairs.py`

Calculates the optimal path from the Player (`@`) to the Stairs (`>`) in a map file using the A\* algorithm. Useful for analyzing map complexity or verifying solvability.

**Usage:**

```bash
python scripts/astar_to_stairs.py <path_to_map_file> [--show-path]
```

- `--show-path`: Visualizes the path on the map output.

### 3. `randomize_effect.py`

Generating randomized variations of sprites. It takes images from `assets/8x8`, applies random hue, brightness, contrast, and saturation adjustments, and saves them to `assets/16x16-randomized-effect` (resizing them to 16x16).

**Configuration (Inside script):**

- `INPUT_FOLDER`: Source directory (default: `assets/8x8`)
- `OUTPUT_FOLDER`: Destination directory (default: `assets/16x16-randomized-effect`)
- `TARGET_SIZE`: Output resolution (default: 16)

**Usage:**

```bash
python scripts/randomize_effect.py
```
