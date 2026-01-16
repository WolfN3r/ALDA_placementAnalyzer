# Initial Placer (03_initial_placer.py)

## Overview

A simple contour-based block placement algorithm that provides initial placement for analog circuit blocks. This placer serves as an initialization step for more sophisticated placement algorithms.

## How It Works

### 1. **Sequential Placement**
- Blocks are placed in the order they appear in the input JSON
- Uses the first variant of each block (sets `is_used` to `true`)
- Grid snapping: 0.005 units (configurable via `GRID_SIZE`)

### 2. **Contour-Based Strategy**

The placer maintains **4 separate contour lines**, one for each device type:
- `nmos1v_nat`
- `nmos2v_nat`
- `pmos1v_nat`
- `pmos2v_nat`

**Important**: Contour lines exist only on the **right and top sides** of placed blocks. All blocks are placed in the **first quadrant** (positive x and y coordinates only).

Each contour tracks the envelope boundary for blocks of different types, ensuring proper spacing constraints are respected.

### 3. **Placement Algorithm**

**First Block:**
- Placed at origin (0, 0) with left-bottom corner of main_bbox aligned

**Subsequent Blocks:**
1. Select appropriate contour line based on block's device type
2. Generate candidate positions from contour (corners on right and top edges)
3. For each candidate:
   - Snap position to grid
   - Ensure coordinates are non-negative (first quadrant constraint)
   - Calculate total bounding box area if block placed there
4. Choose position with minimum total area
5. Update all contour lines with new block's envelopes

**Constraint**: All blocks placed with `x ≥ 0` and `y ≥ 0` (first quadrant only)

### 4. **Evaluation Metrics**

After placement, the algorithm calculates:

- **Area**: Total bounding box area (using max envelopes)
- **Wirelength**: HPWL (Half-Perimeter Wire Length)
  - Pins assumed at block centers
  - For each net: `HPWL = (x_max - x_min) + (y_max - y_min)`
- **Aspect Ratio**: Width / Height of bounding box
- **Cost Function**: Weighted multi-objective function from `layout_analysis.py`
  ```
  Cost = 0.4 × Area + 0.4 × Wirelength + 0.2 × (AspectRatio - 1.0)²
  ```

## Input Format

Expects JSON structure like `blocks_seed42_n5.json`:
```json
{
  "generation_params": {...},
  "technology": "...",
  "blocks": [...],
  "netlist": {...}
}
```

## Output Format

Input JSON with added sections:
```json
{
  ...original input...,
  "placement": {
    "method": "contour_based",
    "grid_size": 0.005,
    "placed_blocks": [
      {
        "block_id": 0,
        "device_type": "nmos1v_nat",
        "position": {"x": 0.0, "y": 0.0},
        "main_bbox": {...},
        "envelope": {...}
      },
      ...
    ]
  },
  "cost_function": {
    "area": 123.456,
    "wirelength": 78.9,
    "aspect_ratio": 1.234,
    "bounding_box": {...},
    "weights": [0.4, 0.4, 0.2],
    "target_aspect_ratio": 1.0,
    "cost": 202.346
  }
}
```

## Usage

### Standalone Mode
```bash
python3 03_initial_placer.py path/to/blocks_seed42_n5.json
```

Output: `blocks_seed42_n5_placed.json` in same directory

### n8n Mode
```bash
cat blocks_seed42_n5.json | python3 03_initial_placer.py
```

Output: JSON to stdout (UTF-8 encoded)

## Dependencies

- **Standard**: `json`, `sys`, `copy`, `pathlib`
- **Custom Libraries** (from `lib/`):
  - `n8n_json_handler.py` - n8n integration
  - `layout_analysis.py` - cost function calculation

## Key Features

✓ Simple and fast initialization
✓ Respects spacing constraints via envelopes
✓ Grid-snapped placement
✓ First quadrant placement (x ≥ 0, y ≥ 0)
✓ Area-minimizing strategy
✓ Dual-mode operation (n8n + standalone)
✓ UTF-8 safe output

## Limitations

- Uses simplified contours (right and top edges only)
- Greedy algorithm (may not find global optimum)
- Assumes pins at block centers
- No overlap checking (relies on envelope constraints)
- First quadrant placement only (x ≥ 0, y ≥ 0)

## Configuration

```python
GRID_SIZE = 0.005  # Manufacturing grid size
```

Modify at top of script if needed.