# Placement Visualization (04_visualize_placement.py)

## Overview

A visualization tool for analog circuit block placement results. Creates visual plots showing block positions with device-type color coding and spacing envelopes.

## Key Features

✓ **Device-Type Color Coding**: Blocks colored by transistor type
✓ **Matching Envelope Colors**: Each device type has consistent colors for blocks and envelopes
✓ **Type Labels**: Device type displayed below each block name
✓ **Metrics Display**: Comprehensive table showing placement quality metrics
✓ **Net Visualization**: Shows connections between blocks (as gray lines)

## Device Type Color Scheme

Each transistor type has a unique, pleasant color scheme with matching envelope colors:

| Device Type | Block Color | Envelope Color | Description |
|-------------|-------------|----------------|-------------|
| `nmos1v_nat` | Light Coral (#FFB6B6) | Red (#FF4444) | N-type MOS, 1V, natural threshold |
| `nmos2v_nat` | Light Green (#B6FFB6) | Green (#44FF44) | N-type MOS, 2V, natural threshold |
| `pmos1v_nat` | Light Blue (#B6B6FF) | Blue (#4444FF) | P-type MOS, 1V, natural threshold |
| `pmos2v_nat` | Light Pink (#FFB6FF) | Magenta (#FF44FF) | P-type MOS, 2V, natural threshold |

## Visualization Layout

### Left Panel: Block Placement
- **Blocks**: Filled rectangles with device-type colors
- **Block Labels**: Block ID (B0, B1, etc.) centered on block
- **Type Labels**: Device type (e.g., "nmos1v_nat") below block ID in italic
- **Envelopes**: Dashed rectangles showing spacing constraints for each device type
- **Nets**: Gray lines connecting block centers (shows circuit connectivity)
- **Bounding Box**: Red solid rectangle showing total layout area

### Right Panel: Metrics Table
- Number of blocks and seed value
- Area, wirelength, and aspect ratio
- Cost function value
- Optimization weights
- Bounding box dimensions

## Input Format

Expects JSON output from `03_initial_placer.py`:
```json
{
  "generation_params": {...},
  "blocks": [...],
  "netlist": {...},
  "placement": {
    "placed_blocks": [
      {
        "block_id": 0,
        "device_type": "nmos1v_nat",
        "position": {...},
        "main_bbox": {...},
        "envelope": {...}
      }
    ]
  },
  "cost_function": {...}
}
```

## Usage

```bash
python3 04_visualize_placement.py <placement_json_file>
```

### Example
```bash
python3 04_visualize_placement.py blocks_seed1_n2_placed.json
```

Output: `blocks_seed1_n2_placed_visualization.png`

## Output

- **Format**: PNG image (300 DPI, publication quality)
- **Dimensions**: 16×8 inches (suitable for reports and presentations)
- **File naming**: `<input_stem>_visualization.png`

## Dependencies

- **Standard Libraries**: `json`, `sys`, `pathlib`
- **Visualization**: `matplotlib` (with `patches` module)

No special or external packages required beyond standard scientific Python stack.

## Technical Details

### Color Consistency
- Block fill color: Light tint of device type color (80% alpha)
- Envelope line color: Saturated version of device type color
- Both use matching hue for visual coherence

### Layout Rendering
- Envelopes drawn with dashed lines (line style `--`)
- Blocks have solid black borders for clarity
- Coordinate system matches the placement coordinate system
- Equal aspect ratio ensures undistorted geometry

### Text Placement
- Block ID: Centered, 1.5 units above center, bold, 11pt
- Device type: Centered, 1.5 units below center, italic, 8pt, dark gray

## Interpretation Guide

**Block Colors** indicate the type of transistor:
- Red tones → NMOS 1V (fastest)
- Green tones → NMOS 2V (higher voltage)
- Blue tones → PMOS 1V (complementary to NMOS 1V)
- Pink tones → PMOS 2V (complementary to NMOS 2V)

**Envelope Overlaps** show spacing constraints:
- Different colored envelopes around each block
- Spacing constraints prevent different device types from overlapping
- Larger spacing for incompatible device types

**Net Lines** show circuit connectivity:
- Gray lines connect blocks that share nets
- Shorter lines indicate better wirelength (lower cost)

## Limitations

- Assumes pins at block centers (simplified model)
- Net visualization shows all-to-all connections (simplified routing)
- No detailed pin-level routing shown
- Single-layer visualization (no 3D stack-up)

## Configuration

To modify colors, edit the `DEVICE_COLORS` dictionary at the top of the script:
```python
DEVICE_COLORS = {
    "nmos1v_nat": ("#FFB6B6", "#FF4444", "--"),  # (block_color, envelope_color, style)
    ...
}
```

## Integration with Placement Flow

Typical workflow:
1. Generate blocks: `01_block_generator.py`
2. Create placement: `03_initial_placer.py`
3. **Visualize results**: `04_visualize_placement.py` ← This script
4. Analyze and iterate

## Examples

### Good Placement
- Compact bounding box
- Short net lines
- Aspect ratio close to target (usually 1.0)
- Minimal envelope overlaps

### Poor Placement
- Large empty spaces
- Long net lines crossing entire layout
- Extreme aspect ratios (very wide or tall)
- Excessive envelope overlaps

## Output Quality

- 300 DPI resolution (publication quality)
- Anti-aliased text and lines
- Tight bounding box (minimal whitespace)
- Professional color scheme suitable for technical reports