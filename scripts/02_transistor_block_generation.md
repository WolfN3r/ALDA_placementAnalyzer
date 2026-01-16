# Transistor Block Generator

## Overview
This script generates random transistor blocks for analog IC design based on technology constraints and creates realistic netlists connecting them. It works both as a standalone tool and integrated with n8n workflows.

**What it does:**
1. Generates N transistor blocks with random parameters (W, L, multiplier, fingers)
2. Creates layout variants for each block (different row/column arrangements)
3. Generates a netlist connecting blocks through pin clusters
4. All results are reproducible using seed-based random generation

**Output:** JSON file containing blocks with layout variants and a netlist with electrical connections.

## Quick Start

```bash
# Generate 10 blocks with seed 42
python3 transistor_block_generator.py 10 42

# Output saved to: json_files/blocks_seed42_n10.json
```

## Dependencies

**Python 3.6+** with standard library only:
- `json` - JSON handling
- `random` - Seeded random generation
- `sys`, `os`, `pathlib` - File system operations

**Required files:**
- `lib/n8n_json_handler.py` - n8n communication handler
- `lib/gpdk090_tech_simple.json` - Technology constraints
- `lib/generation_config.json` - Tunable parameters

## Setup

1. **Directory structure:**
   ```
   project/
   ├── transistor_block_generator.py
   ├── lib/
   │   ├── n8n_json_handler.py
   │   ├── gpdk090_tech_simple.json
   │   └── generation_config.json
   └── json_files/  (created automatically)
   ```

2. **Configure parameters** in `lib/generation_config.json`:
   ```json
   {
     "generation_params": {
       "length_range": { "step": 0.01 },
       "width_range": { "step": 0.05 },
       "multiplier_range": { "min": 2, "max": 16 },
       "aspect_ratio": { ... }
     },
     "netlist": {
       "density": 2.5,
       "pins_per_block_min": 3,
       "pins_per_block_max": 6
     }
   }
   ```

3. **Run:**
   ```bash
   python3 transistor_block_generator.py <num_blocks> <seed>
   ```

## Features
- Generates multiple transistor blocks with random parameters
- Uses seeded random generation for reproducible results
- Validates against technology constraints
- Creates all valid layout variants with aspect ratio filtering
- Generates spacing envelopes for inter-device placement
- **Generates realistic netlists with clustered connections**
- Supports both n8n integration and standalone usage
- **Grid snapping**: All dimensions are snapped to manufacturing grid
- **Even multipliers**: Uses even numbers (2, 4, 6, 8, ...) for more variability
- **Variant validation**: Ensures at least one valid variant per block
- **Configurable parameters**: External JSON configuration for easy tuning
- **Variant tracking**: Each variant has `is_used` field for placement tracking

## Directory Structure
```
.
├── transistor_block_generator.py  # Main script
├── lib/                            # Libraries and tech files
│   ├── n8n_json_handler.py        # n8n communication handler
│   ├── gpdk090_tech_simple.json   # Technology file
│   └── generation_config.json     # Tunable generation parameters
└── json_files/                     # Output directory (standalone mode)
```

## Usage

### Standalone Mode
Run the script with command line arguments:

```bash
python3 transistor_block_generator.py <num_of_blocks> <seed>
```

**Example:**
```bash
python3 transistor_block_generator.py 5 42
```

This will:
1. Load technology file from `lib/gpdk090_tech_simple.json`
2. Load configuration from `lib/generation_config.json`
3. Generate 5 blocks with seed 42
4. Save output to `json_files/blocks_seed42_n5.json`

### N8n Mode
Use in n8n workflow by piping JSON input through stdin:

```bash
cat input.json | python3 transistor_block_generator.py > output.json
```

**Input JSON format** (combines tech file + generation parameters):
```json
{
  "technology_info": {...},
  "device_constraints": {...},
  "physical_design_rules": {...},
  "inter_device_spacing_matrix": {...},
  "gen_params": {
    "num_of_blocks": 10,
    "seed": 42
  }
}
```

## Configuration File

The `lib/generation_config.json` file contains tunable parameters for the generation process:

```json
{
  "generation_params": {
    "length_range": {
      "max_fraction": 0.2,
      "step": 0.01
    },
    "width_range": {
      "max_fraction": 0.1,
      "step": 0.05
    },
    "multiplier_range": {
      "min": 2,
      "max": 16
    },
    "num_fingers_range": {
      "min": 1,
      "max": 4
    },
    "aspect_ratio": {
      "min_aspect_min": 0.3,
      "min_aspect_max": 0.8,
      "max_aspect_min": 1.2,
      "max_aspect_max": 3.0
    }
  },
  "validation": {
    "max_generation_attempts": 10
  }
}
```

### Configuration Parameters

- **length_range.max_fraction**: Maximum length as fraction of device max (0.2 = 20%)
- **length_range.step**: Step size for length quantization (default: 0.01 µm = 10nm)
- **width_range.max_fraction**: Maximum width as fraction of device max (0.1 = 10%)
- **width_range.step**: Step size for width quantization (default: 0.05 µm = 50nm)
- **multiplier_range.min/max**: Range for even multipliers (2, 4, 6, 8, ...)
- **num_fingers_range.min/max**: Range for number of fingers per transistor
- **aspect_ratio**: Random ranges for min/max aspect ratios
- **validation.max_generation_attempts**: Maximum attempts to generate valid block

**Important**: Width and length are snapped to their respective `step` values (not the manufacturing grid). This allows designers to use multiples of minimum dimensions. All other dimensions (bounding boxes, spacing envelopes) are still snapped to the manufacturing grid.

## Netlist Generation

The script automatically generates a netlist that connects blocks through pin clusters, simulating real IC connectivity.

### How It Works

1. **Pin Assignment**: Each block gets 3-6 pins (configurable)
   - Pin naming: `B{block_id}_P{pin_id}` (e.g., B0_P0, B1_P2)

2. **Net Creation**: Pins are grouped into electrical nets
   - Each net connects 2-4 pins from different blocks
   - Target number of nets: `density × num_blocks`
   - Example: 10 blocks × 2.5 density = 25 nets

3. **Clustering**: Ensures realistic connectivity
   - Each block has at least 2 connections
   - Pins can only belong to one net
   - Multiple pins from same block can share a net

### Configuration
```json
{
  "netlist": {
    "density": 2.5,           // Nets per block (higher = more connections)
    "pins_per_block_min": 3,  // Minimum pins per block
    "pins_per_block_max": 6   // Maximum pins per block
  }
}
```

### Output Format
```json
{
  "netlist": {
    "num_nets": 12,
    "num_pins": 27,
    "density": 2.4,
    "nets": [
      {
        "net_id": "net_0",
        "pins": ["B0_P0", "B2_P1", "B4_P3"]  // Connects blocks 0, 2, and 4
      }
    ]
  }
}
```

### Usage in Placement
- Use nets to calculate wirelength
- Identify which blocks need to be close together
- Each net represents an electrical connection that needs routing

## Output Structure

### Output JSON Format
```json
{
  "generation_params": {
    "num_of_blocks": 5,
    "seed": 42
  },
  "technology": "gpdk090_simple_tech",
  "blocks": [
    {
      "block_id": 0,
      "device_type": "nmos1v_nat",
      "parameters": {
        "width": 2.835,
        "length": 0.15,
        "multiplier": 8,
        "num_fingers": 2,
        "total_fingers": 16
      },
      "variants": [
        {
          "layout": {
            "rows": 4,
            "cols": 4,
            "aspect_ratio": 1.315,
            "arrangement": [[0,1,2,3], [4,5,6,7], [8,9,10,11], [12,13,14,15]]
          },
          "matching_scheme": [[0,7], [1,6], [2,5], [3,4]],
          "main_bbox": {
            "x_min": 0.0,
            "y_min": 0.0,
            "x_max": 7.93,
            "y_max": 6.03
          },
          "spacing_envelopes": {
            "nmos1v_nat": {...},
            "nmos2v_nat": {...},
            "pmos1v_nat": {...},
            "pmos2v_nat": {...}
          },
          "is_used": false
        }
      ],
      "generation_attempts": 1
    }
  ],
  "netlist": {
    "num_nets": 12,
    "num_pins": 27,
    "density": 2.4,
    "nets": [
      {
        "net_id": "net_0",
        "pins": ["B0_P0", "B2_P1", "B4_P3"]
      }
    ]
  }
}
```

### Block Information
- `block_id`: Sequential identifier
- `device_type`: Transistor type (nmos1v_nat, nmos2v_nat, pmos1v_nat, pmos2v_nat)
- `parameters`: Physical parameters (W, L, M, NF) - **all snapped to grid**
- `generation_attempts`: Number of attempts needed to generate valid block

### Layout Variants
Each block can have multiple valid layout variants:
- `rows` × `cols`: Grid dimensions
- `aspect_ratio`: Width/height ratio
- `arrangement`: 2D array of finger indices
- `matching_scheme`: Paired transistors for matching (symmetrical)
- **`is_used`**: Boolean flag for tracking variant usage (default: false)

### Bounding Boxes
- `main_bbox`: Core device area (x_min, y_min, x_max, y_max)
- `spacing_envelopes`: Safe spacing to each device type

## Key Features Explained

### Grid Snapping vs Step Snapping

**Width and Length (W/L)**: Snapped to configurable step sizes defined in `generation_config.json`:
```json
"length_range": {
  "step": 0.01  // Length snapped to 10nm steps
},
"width_range": {
  "step": 0.05  // Width snapped to 50nm steps
}
```

**All Other Dimensions**: Snapped to manufacturing grid from technology file:
```json
"technology_info": {
  "manufacturing_grid": 0.005,  // 5nm grid
  "units": "um"
}
```

This separation allows designers to use multiples of minimum W/L (e.g., 0.05 µm steps for width) while ensuring all layout coordinates are on the manufacturing grid (0.005 µm).

**Example:**
- Width: 2.85 µm (step 0.05)
- Length: 0.15 µm (step 0.01)
- BBox x_max: 7.935 µm (grid 0.005)

### Even Multipliers
The script uses even numbers (2, 4, 6, 8, 10, ...) instead of just powers of 2. This provides more variability:
- M=2: Simple pair
- M=4: Two pairs
- M=6: Three pairs (less common but valid)
- M=8: Four pairs
- etc.

### Variant Validation
If a parameter combination doesn't produce any valid variants (due to aspect ratio constraints), the script automatically retries with new random parameters up to `max_generation_attempts` times.

### Variant Tracking
Each variant includes an `is_used` field (default: false). This allows placement algorithms to mark which variant was selected:
```json
{
  "layout": {...},
  "matching_scheme": [...],
  "main_bbox": {...},
  "spacing_envelopes": {...},
  "is_used": false  // Set to true when variant is selected for placement
}
```

## Error Handling

If a block fails to generate after max attempts, the output includes:
```json
{
  "block_id": X,
  "error": "Error message",
  "generation_attempts": 10,
  "parameters": {...}
}
```

## Testing

Test standalone mode:
```bash
python3 transistor_block_generator.py 5 42
```

Test n8n mode:
```bash
cat test_n8n_input.json | python3 transistor_block_generator.py > test_output.json
```

Verify grid snapping:
```bash
python3 -c "
import json
with open('json_files/blocks_seed42_n5.json') as f:
    data = json.load(f)
width = data['blocks'][0]['parameters']['width']
grid = 0.005
print(f'Width: {width}')
print(f'Grid aligned: {(width / grid) % 1 == 0}')
"
```

## Troubleshooting

### No variants generated
- **Cause**: Aspect ratio constraints too strict for given W/L
- **Fix**: Widen aspect ratio range in config or adjust W/L ranges

### Low netlist density
- **Cause**: Not enough pins or too few blocks
- **Fix**: Increase `pins_per_block_max` or `density` in config

### Script hangs
- **Cause**: Infinite loop in generation (should not happen with current code)
- **Fix**: Check `max_generation_attempts` in config

### Dimensions not on grid
- **Cause**: W/L use step, not grid (this is intentional)
- **Check**: Layout dimensions (`main_bbox`) should be on grid (0.005)

### Import errors
- **Cause**: Missing lib directory or files
- **Fix**: Ensure `lib/n8n_json_handler.py` and config files exist

## Dependencies

- Python 3.6+
- Standard library only: `json`, `random`, `sys`, `os`, `pathlib`
- `n8n_json_handler` (included in lib/)

## What to Look For When Revisiting This Code

### In `generation_config.json`:
1. **Step sizes** (`length_range.step`, `width_range.step`) - Controls W/L quantization
   - Larger steps = coarser dimensions (easier to work with)
   - Smaller steps = finer control (more options)

2. **Multiplier range** (`multiplier_range.min/max`) - Device sizing
   - Even numbers only (2, 4, 6, ...)
   - Higher max = larger devices possible

3. **Aspect ratio constraints** - Block shape limits
   - Low min_aspect = allow tall/thin blocks
   - High max_aspect = allow wide blocks

4. **Netlist density** - Connection complexity
   - `density = 2.5` means ~2.5 nets per block
   - Higher = more interconnected (harder placement)

### In output JSON:
1. **`blocks[].variants[]`** - Different layout options for each block
   - More variants = more placement flexibility
   - Check `is_used` field to track which variant was selected

2. **`netlist.nets[]`** - Electrical connections
   - Each net shows which blocks need to be connected
   - Use for wirelength calculation and routing

3. **`main_bbox`** vs **`spacing_envelopes`**:
   - `main_bbox` = actual device area
   - `spacing_envelopes` = keep-out zones for different device types

### Function naming:
- All generation functions start with `wmi_` prefix
- `wmi_generate_random_blocks()` - Main entry point
- `wmi_generate_transistor_block()` - Single block generation
- `wmi_generate_netlist()` - Netlist creation

## Notes

- All dimensions are in micrometers (µm)
- Width and Length are snapped to configurable steps (default: W=0.05µm, L=0.01µm)
- All other dimensions (bounding boxes, spacing) are snapped to manufacturing grid (0.005 µm)
- Aspect ratio is calculated as width/height
- UTF-8 encoding is ensured for n8n compatibility
- Multiplier uses even numbers for better matching variability
- Each block is guaranteed to have at least one valid variant
- Seed ensures reproducible random generation
- Configuration is externalized in `generation_config.json` for easy tuning
- No verbose output by default (runs silently in background)