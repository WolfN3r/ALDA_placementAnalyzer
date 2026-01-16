#!/usr/bin/env python3
"""
Initial Placer - Simple contour-based block placement
Places blocks sequentially to minimize total area
Works with n8n or standalone
"""

import json
import sys
import copy
from pathlib import Path

# Import libraries from lib directory
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor
from layout_analysis import wmi_calculate_cost

# Configuration
GRID_SIZE = 0.005


def snap_to_grid(value, grid=GRID_SIZE):
    """Round value to grid"""
    return round(round(value / grid) * grid, 6)


class ContourLine:
    """Represents a contour line for a specific device type (right and top sides only)"""
    
    def __init__(self, device_type):
        self.device_type = device_type
        self.segments = []  # List of (x, y) points defining the contour
    
    def add_block_envelope(self, envelope):
        """Add a block's envelope to update the contour"""
        if not self.segments:
            # First block - initialize contour with right and top edges only
            self.segments = [
                (envelope["x_max"], 0.0),  # Right edge starts at bottom
                (envelope["x_max"], envelope["y_max"]),  # Right edge top corner
                (0.0, envelope["y_max"])  # Top edge ends at left
            ]
        else:
            # Merge envelope with existing contour
            self._merge_envelope(envelope)
    
    def _merge_envelope(self, env):
        """Merge new envelope with existing contour (right and top sides only)"""
        # Get current max extents
        all_x = [p[0] for p in self.segments] + [env["x_max"]]
        all_y = [p[1] for p in self.segments] + [env["y_max"]]
        
        x_max = max(all_x)
        y_max = max(all_y)
        
        # Rebuild contour: right edge and top edge starting from origin
        self.segments = [
            (x_max, 0.0),  # Right edge bottom
            (x_max, y_max),  # Right edge top corner
            (0.0, y_max)  # Top edge to left
        ]
    
    def get_candidate_positions(self):
        """Get candidate positions for next block (right and top edge corners)"""
        if not self.segments:
            return [(0.0, 0.0)]
        
        # Return positions along right and top edges
        candidates = list(self.segments)
        return candidates


def calculate_bounding_box(placed_blocks):
    """Calculate bounding box of all placed blocks using max envelope"""
    if not placed_blocks:
        return {"x_min": 0.0, "y_min": 0.0, "x_max": 0.0, "y_max": 0.0}
    
    all_envelopes = []
    for block in placed_blocks:
        # Find max envelope
        max_envelope = None
        max_area = 0
        for env_type, env in block["envelope"].items():
            area = (env["x_max"] - env["x_min"]) * (env["y_max"] - env["y_min"])
            if area > max_area:
                max_area = area
                max_envelope = env
        
        if max_envelope:
            all_envelopes.append(max_envelope)
    
    if not all_envelopes:
        return {"x_min": 0.0, "y_min": 0.0, "x_max": 0.0, "y_max": 0.0}
    
    # Bounding box starts at origin (first quadrant only)
    x_min = 0.0
    y_min = 0.0
    x_max = max(e["x_max"] for e in all_envelopes)
    y_max = max(e["y_max"] for e in all_envelopes)
    
    return {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max}


def calculate_area(placed_blocks):
    """Calculate total bounding box area"""
    bbox = calculate_bounding_box(placed_blocks)
    width = bbox["x_max"] - bbox["x_min"]
    height = bbox["y_max"] - bbox["y_min"]
    return width * height


def calculate_hpwl(netlist, placed_blocks):
    """Calculate Half-Perimeter Wire Length"""
    # Create pin location map (center of each block)
    pin_locations = {}
    for block in placed_blocks:
        block_id = block["block_id"]
        bbox = block["main_bbox"]
        center_x = (bbox["x_min"] + bbox["x_max"]) / 2.0
        center_y = (bbox["y_min"] + bbox["y_max"]) / 2.0
        
        # Map all pins of this block to center
        for net in netlist["nets"]:
            for pin in net["pins"]:
                if pin.startswith(f"B{block_id}_"):
                    pin_locations[pin] = (center_x, center_y)
    
    # Calculate HPWL for each net
    total_hpwl = 0.0
    for net in netlist["nets"]:
        if len(net["pins"]) < 2:
            continue
        
        x_coords = []
        y_coords = []
        for pin in net["pins"]:
            if pin in pin_locations:
                x, y = pin_locations[pin]
                x_coords.append(x)
                y_coords.append(y)
        
        if len(x_coords) >= 2:
            hpwl = (max(x_coords) - min(x_coords)) + (max(y_coords) - min(y_coords))
            total_hpwl += hpwl
    
    return total_hpwl


def place_blocks(blocks_data):
    """Main placement function using contour-based approach"""
    blocks = blocks_data["blocks"]
    
    # Initialize contour lines for each device type
    contours = {
        "nmos1v_nat": ContourLine("nmos1v_nat"),
        "nmos2v_nat": ContourLine("nmos2v_nat"),
        "pmos1v_nat": ContourLine("pmos1v_nat"),
        "pmos2v_nat": ContourLine("pmos2v_nat")
    }
    
    placed_blocks = []
    
    for block in blocks:
        if "error" in block:
            continue
        
        if not block["variants"]:
            continue
        
        # Use first variant
        variant = block["variants"][0]
        variant["is_used"] = True
        
        device_type = block["device_type"]
        main_bbox = variant["main_bbox"]
        spacing_envelopes = variant["spacing_envelopes"]
        
        # First block: place at origin
        if not placed_blocks:
            position = (0.0, 0.0)
        else:
            # Get contour for this device type
            contour = contours[device_type]
            candidates = contour.get_candidate_positions()
            
            # Try each candidate position and find best (minimum area)
            best_position = None
            best_area = float('inf')
            
            for candidate in candidates:
                # Snap to grid and ensure positive coordinates (first quadrant only)
                test_x = max(0.0, snap_to_grid(candidate[0]))
                test_y = max(0.0, snap_to_grid(candidate[1]))
                
                # Create test placement
                test_placed = placed_blocks + [{
                    "block_id": block["block_id"],
                    "device_type": device_type,
                    "position": {"x": test_x, "y": test_y},
                    "main_bbox": {
                        "x_min": test_x,
                        "y_min": test_y,
                        "x_max": test_x + (main_bbox["x_max"] - main_bbox["x_min"]),
                        "y_max": test_y + (main_bbox["y_max"] - main_bbox["y_min"])
                    },
                    "envelope": {
                        env_type: {
                            "x_min": test_x + env["x_min"],
                            "y_min": test_y + env["y_min"],
                            "x_max": test_x + env["x_max"],
                            "y_max": test_y + env["y_max"]
                        }
                        for env_type, env in spacing_envelopes.items()
                    }
                }]
                
                # Calculate area
                area = calculate_area(test_placed)
                
                if area < best_area:
                    best_area = area
                    best_position = (test_x, test_y)
            
            position = best_position if best_position else (0.0, 0.0)
        
        # Place block at chosen position
        placed_block = {
            "block_id": block["block_id"],
            "device_type": device_type,
            "position": {"x": position[0], "y": position[1]},
            "main_bbox": {
                "x_min": position[0],
                "y_min": position[1],
                "x_max": position[0] + (main_bbox["x_max"] - main_bbox["x_min"]),
                "y_max": position[1] + (main_bbox["y_max"] - main_bbox["y_min"])
            },
            "envelope": {
                env_type: {
                    "x_min": position[0] + env["x_min"],
                    "y_min": position[1] + env["y_min"],
                    "x_max": position[0] + env["x_max"],
                    "y_max": position[1] + env["y_max"]
                }
                for env_type, env in spacing_envelopes.items()
            }
        }
        
        placed_blocks.append(placed_block)
        
        # Update all contours with this block's envelopes
        for env_type, env in placed_block["envelope"].items():
            contours[env_type].add_block_envelope(env)
    
    return placed_blocks


def evaluate_placement(blocks_data, placed_blocks):
    """Evaluate placement quality"""
    # Calculate metrics
    area = calculate_area(placed_blocks)
    wirelength = calculate_hpwl(blocks_data["netlist"], placed_blocks)
    
    bbox = calculate_bounding_box(placed_blocks)
    width = bbox["x_max"] - bbox["x_min"]
    height = bbox["y_max"] - bbox["y_min"]
    aspect_ratio = width / height if height > 0 else 1.0
    
    # Cost function weights (balanced)
    weights = (0.4, 0.4, 0.2)
    target_ar = 1.0
    
    # Calculate cost (using area and wirelength as normalization)
    cost = wmi_calculate_cost(
        area=area,
        wirelength=wirelength,
        aspect_ratio=aspect_ratio,
        init_area=1.0,
        init_wirelength=1.0,
        target_ar=target_ar,
        weights=weights
    )
    
    return {
        "area": round(area, 6),
        "wirelength": round(wirelength, 6),
        "aspect_ratio": round(aspect_ratio, 6),
        "bounding_box": bbox,
        "weights": weights,
        "target_aspect_ratio": target_ar,
        "cost": round(cost, 6)
    }


def process_placement(json_data):
    """Main processing function"""
    # Deep copy to avoid modifying input
    result = copy.deepcopy(json_data)
    
    # Perform placement
    placed_blocks = place_blocks(result)
    
    # Evaluate placement
    cost_function = evaluate_placement(result, placed_blocks)
    
    # Add placement info to result
    result["placement"] = {
        "method": "contour_based",
        "grid_size": GRID_SIZE,
        "placed_blocks": placed_blocks
    }
    
    result["cost_function"] = cost_function
    
    return result


def process_n8n_input(json_data):
    """Process input from n8n"""
    result = process_placement(json_data)
    # Ensure UTF-8 safe output
    return json.loads(json.dumps(result, ensure_ascii=False))


def main_standalone(input_file):
    """Run standalone with input JSON file"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Load input
    with open(input_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Process placement
    result = process_placement(json_data)
    
    # Save output to current directory
    output_file = Path.cwd() / f"{input_path.stem}_placed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Placement completed!")
    print(f"Output saved to: {output_file}")
    print(f"Total area: {result['cost_function']['area']:.6f}")
    print(f"Wirelength: {result['cost_function']['wirelength']:.6f}")
    print(f"Aspect ratio: {result['cost_function']['aspect_ratio']:.6f}")
    print(f"Cost: {result['cost_function']['cost']:.6f}")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        # Standalone mode with input file
        main_standalone(sys.argv[1])
    elif len(sys.argv) == 1:
        # n8n mode (no arguments)
        n8n_processor = create_n8n_processor(process_n8n_input)
        n8n_processor()
    else:
        print("Usage:")
        print("  Standalone: python3 03_initial_placer.py <input_json_file>")
        print("  n8n mode: cat input.json | python3 03_initial_placer.py")
        sys.exit(1)