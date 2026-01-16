# Placement Visualizer (04_placement_visualizer.py)

## Overview

A simple visualizer for analog circuit block placement that shows the physical layout with envelopes, nets, and key metrics.

## Configuration

```python
DISPLAY_MODE = 0  # 0 = save PNG, 1 = show with Xming
```

Set `DISPLAY_MODE = 1` to display with Xming on your computer.
Set `DISPLAY_MODE = 0` to save PNG files to `placement/` directory.

## Features

### Left Panel: Block Placement
- **Blocks**: Filled rectangles with distinct colors, labeled as B0, B1, B2, etc.
- **Main Bounding Box (main_bbox)**: The actual block outline
- **Envelopes**: Four types shown as dashed contours:
  - `nmos1v_nat`: Red dashed line
  - `nmos2v_nat`: Green dashed line
  - `pmos1v_nat`: Blue dashed line
  - `pmos2v_nat`: Magenta dashed line
- **Nets**: Colored lines connecting block centers according to netlist
- **Bounding Box**: Red solid rectangle showing total layout bounds
  - Surrounds ALL envelopes from all four sides
  - Starts at origin (0, 0) after coordinate shifting

### Right Panel: Metrics Table
- Generation parameters (blocks count, seed)
- Cost function result
- Area, wirelength (HPWL), aspect ratio
- Weights breakdown
- Bounding box dimensions

## Key Features

✓ Automatic coordinate shifting (ensures all blocks visible in first quadrant)
✓ Correct bounding box (surrounds all envelopes, starts at origin)
✓ Color-coded envelopes with legend
✓ Net visualization between connected blocks
✓ Clear layering (nets → envelopes → blocks → bounding box)
✓ Compact table display (50% smaller)
✓ High-resolution output (300 DPI PNG)
✓ Dual display mode (Xming / save PNG)
✓ Dual-mode operation (n8n + standalone)

## Usage

### Display Mode Configuration

Edit the `DISPLAY_MODE` variable at the top of the script:
- `DISPLAY_MODE = 0`: Save PNG to `placement/` directory
- `DISPLAY_MODE = 1`: Show with Xming (interactive display)

### Standalone Mode (Save PNG)
```bash
python3 04_placement_visualizer.py <placed_blocks.json>
```

Output:
- Displays JSON with generation_params and cost_function
- Saves visualization to `init_placement/init_placement_seed<X>_n<N>.png`
- Directory is created relative to the script location

Example: `init_placement/init_placement_seed42_n5.png`

### Standalone Mode (Show with Xming)
1. Set `DISPLAY_MODE = 1` in the script
2. Ensure Xming is running on your Windows machine
3. Set DISPLAY environment variable on WSL: `export DISPLAY=:0`
4. Run: `python3 04_placement_visualizer.py <placed_blocks.json>`

### n8n Mode
```bash
cat placed_blocks.json | python3 04_placement_visualizer.py
```

Output:
- JSON to stdout with generation_params and cost_function
- Saves visualization based on DISPLAY_MODE setting

## Input Format

Expects JSON from `03_initial_placer.py` output with structure:
```json
{
  "generation_params": {...},
  "placement": {
    "placed_blocks": [...]
  },
  "cost_function": {...},
  "netlist": {...}
}
```

## Output Format

Returns simplified JSON:
```json
{
  "generation_params": {
    "num_of_blocks": 5,
    "seed": 42
  },
  "cost_function": {
    "area": 4269.8424,
    "wirelength": 475.775,
    "aspect_ratio": 0.313041,
    "bounding_box": {...},
    "weights": [0.4, 0.4, 0.2],
    "target_aspect_ratio": 1.0,
    "cost": 1898.341343
  },
  "visualization_saved": "init_placement/init_placement_seed42_n5.png"
}
```

Note: `visualization_saved` field only present when `DISPLAY_MODE = 0`

## Dependencies

- **Standard**: `json`, `sys`, `colorsys`, `pathlib`
- **Matplotlib**: For visualization
- **Custom Libraries** (from `lib/`):
  - `n8n_json_handler.py` - n8n integration

## Color Scheme

### Envelopes (Fixed)
- `nmos1v_nat`: Red (#FF0000)
- `nmos2v_nat`: Green (#00FF00)
- `pmos1v_nat`: Blue (#0000FF)
- `pmos2v_nat`: Magenta (#FF00FF)

### Blocks & Nets
- Generated using golden ratio HSV distribution for maximum distinction

## Visual Hierarchy (Z-order)

1. Background: Grid
2. Nets (z=0): Behind everything
3. Envelopes (z=1): Dashed contours
4. Block fills (z=2): Colored rectangles
5. Block labels (z=3): Text "B0", "B1", etc.
6. Bounding box (z=4): Red outline on top

## Example Output

The visualizer produces a two-panel figure:
- **Left**: Physical layout with all geometric details
- **Right**: Tabular metrics summary

Perfect for:
- Quick visual inspection of placement quality
- Debugging placement algorithms
- Documenting results
- Comparing different placements

## Notes

- Automatic shifting ensures all coordinates are positive (first quadrant)
- Bounding box correctly calculated to surround ALL envelopes after shift
- Bounding box always starts at origin (0, 0) after coordinate shift
- Envelopes may extend beyond blocks (normal behavior for spacing constraints)
- Net connections use block centers (pin positions not specified in current format)
- Table is compact with 50% narrower columns and 20% larger font than original compressed version
- PNG files saved to `init_placement/` directory (created in script's directory)
- PNG output filenames: `init_placement_seed<X>_n<N>.png` where X=seed, N=num_blocks