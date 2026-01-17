#!/usr/bin/env python3
"""
Improved Gravity-Based Placer with Aspect Ratio Control
Blocks drop down and slide left to minimize dead space
"""

import json
import sys
import copy
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor

GRID_SIZE = 0.005
MAX_GRAVITY_ITERATIONS = 5


def snap_to_grid(value, grid=GRID_SIZE):
    """Snap value to grid"""
    return round(round(value / grid) * grid, 6)


def wmi_calculate_cost(area, wirelength, aspect_ratio, init_area,
                       init_wirelength, target_ar, weights):
    """Simple cost function without numpy"""
    w0, w1, w2 = weights
    cost = (w0 * (area / init_area) +
            w1 * (wirelength / init_wirelength) +
            w2 * (aspect_ratio - target_ar) ** 2)
    return float(cost)


def find_y_with_envelope(placed_blocks, device_type, spacing_envelope, x_pos):
    """Find minimum Y where block can be placed considering spacing envelopes"""
    max_y = 0.0
    
    env_x_min = x_pos + spacing_envelope["x_min"]
    env_x_max = x_pos + spacing_envelope["x_max"]
    
    for pb in placed_blocks:
        pb_env = pb["envelope"][device_type]
        
        # Check horizontal overlap
        if not (env_x_max <= pb_env["x_min"] or env_x_min >= pb_env["x_max"]):
            # Envelopes overlap horizontally, must stack vertically
            max_y = max(max_y, pb_env["y_max"])
    
    return max_y


def apply_vertical_gravity(placed_blocks, device_type, spacing_envelope, x_pos):
    """Drop block down to lowest valid position"""
    env_y_min = find_y_with_envelope(placed_blocks, device_type, spacing_envelope, x_pos)
    block_y = env_y_min - spacing_envelope["y_min"]
    return max(0.0, snap_to_grid(block_y))


def apply_horizontal_gravity(placed_blocks, device_type, spacing_envelope, x_pos, y_pos):
    """Slide block left to leftmost valid position"""
    env_y_min = y_pos + spacing_envelope["y_min"]
    env_y_max = y_pos + spacing_envelope["y_max"]
    
    # Find maximum x that blocks leftward movement
    max_blocking_x = 0.0
    
    for pb in placed_blocks:
        pb_env = pb["envelope"][device_type]
        
        # Check vertical overlap
        if not (env_y_max <= pb_env["y_min"] or env_y_min >= pb_env["y_max"]):
            # Envelopes overlap vertically
            if pb_env["x_max"] <= x_pos + spacing_envelope["x_min"]:
                # This block is to the left and blocks us
                max_blocking_x = max(max_blocking_x, pb_env["x_max"])
    
    # Block position from envelope constraint
    new_x = max_blocking_x - spacing_envelope["x_min"]
    return max(0.0, snap_to_grid(new_x))


def apply_gravity(placed_blocks, device_type, spacing_envelope, x_pos, y_pos):
    """Apply both vertical and horizontal gravity iteratively"""
    current_x, current_y = x_pos, y_pos
    
    for _ in range(MAX_GRAVITY_ITERATIONS):
        # Vertical gravity (drop down)
        new_y = apply_vertical_gravity(placed_blocks, device_type, spacing_envelope, current_x)
        
        # Horizontal gravity (slide left)
        new_x = apply_horizontal_gravity(placed_blocks, device_type, spacing_envelope, current_x, new_y)
        
        # Check convergence
        if abs(new_x - current_x) < 0.001 and abs(new_y - current_y) < 0.001:
            break
        
        current_x, current_y = new_x, new_y
    
    return current_x, current_y


def calculate_bbox(placed_blocks):
    """Calculate total bounding box"""
    if not placed_blocks:
        return {"x_min": 0.0, "y_min": 0.0, "x_max": 0.0, "y_max": 0.0}
    
    x_max = max(env["x_max"] for b in placed_blocks for env in b["envelope"].values())
    y_max = max(env["y_max"] for b in placed_blocks for env in b["envelope"].values())
    
    return {"x_min": 0.0, "y_min": 0.0, "x_max": x_max, "y_max": y_max}


def evaluate_position(placed_blocks, test_block):
    """Score a potential placement position"""
    test_placed = placed_blocks + [test_block]
    bbox = calculate_bbox(test_placed)
    
    area = bbox["x_max"] * bbox["y_max"]
    aspect = bbox["x_max"] / bbox["y_max"] if bbox["y_max"] > 0 else 1.0
    
    # Calculate block areas (for dead space calculation)
    total_block_area = sum(
        (b["main_bbox"]["x_max"] - b["main_bbox"]["x_min"]) *
        (b["main_bbox"]["y_max"] - b["main_bbox"]["y_min"])
        for b in placed_blocks
    )
    block_w = test_block["main_bbox"]["x_max"] - test_block["main_bbox"]["x_min"]
    block_h = test_block["main_bbox"]["y_max"] - test_block["main_bbox"]["y_min"]
    total_block_area += block_w * block_h
    
    dead_space = area - total_block_area
    
    # VERY strong aspect ratio preference - we want square layouts!
    # Penalize deviation from 1.0 extremely heavily
    aspect_deviation = abs(aspect - 1.0)
    
    if aspect < 0.5 or aspect > 2.0:
        # Reject extreme aspect ratios with huge penalty
        aspect_penalty = 1000.0 * aspect_deviation
    elif aspect < 0.7 or aspect > 1.5:
        # Heavy penalty for moderately bad aspect ratios
        aspect_penalty = 50.0 * aspect_deviation ** 2
    else:
        # Moderate penalty for slightly off aspect ratios
        aspect_penalty = 15.0 * aspect_deviation ** 2
    
    # Score: area is important, but aspect ratio is critical!
    score = area * (1.0 + aspect_penalty) + 0.15 * dead_space
    
    return score


def get_candidate_x_positions(placed_blocks):
    """Generate candidate x positions from placed blocks"""
    candidates = [0.0]
    
    for pb in placed_blocks:
        # Add positions from all envelope types for more options
        for env in pb["envelope"].values():
            candidates.append(env["x_max"])
            # Also try positions slightly before the envelope edge
            if env["x_max"] > 0:
                candidates.append(env["x_max"] * 0.5)
    
    # Remove duplicates, sort, and snap to grid
    unique_candidates = sorted(set(snap_to_grid(x) for x in candidates))
    
    # If too many candidates, sample evenly
    if len(unique_candidates) > 15:
        step = len(unique_candidates) // 15
        unique_candidates = [unique_candidates[0]] + unique_candidates[1::step] + [unique_candidates[-1]]
    
    return unique_candidates


def place_blocks(blocks_data):
    """Main placement function using gravity-based algorithm"""
    blocks = blocks_data["blocks"]
    
    # Sort blocks by area (largest first) for better packing
    blocks_with_area = []
    for block in blocks:
        if "error" not in block and block["variants"]:
            variant = block["variants"][0]
            bbox = variant["main_bbox"]
            area = (bbox["x_max"] - bbox["x_min"]) * (bbox["y_max"] - bbox["y_min"])
            blocks_with_area.append((area, block))
    
    # Sort by area descending
    blocks_with_area.sort(key=lambda x: x[0], reverse=True)
    sorted_blocks = [b for _, b in blocks_with_area]
    
    placed_blocks = []
    
    for block in sorted_blocks:
        if "error" in block or not block["variants"]:
            continue
        
        # Use first variant
        variant = block["variants"][0]
        variant["is_used"] = True
        
        device_type = block["device_type"]
        main_bbox = variant["main_bbox"]
        spacing_envelopes = variant["spacing_envelopes"]
        
        block_w = main_bbox["x_max"] - main_bbox["x_min"]
        block_h = main_bbox["y_max"] - main_bbox["y_min"]
        envelope = spacing_envelopes[device_type]
        
        # First block at origin
        if not placed_blocks:
            best_x, best_y = 0.0, 0.0
        else:
            # Generate candidate positions with aggressive aspect ratio control
            candidates = get_candidate_x_positions(placed_blocks)
            
            # Check current layout aspect ratio
            if placed_blocks:
                bbox_current = calculate_bbox(placed_blocks)
                current_aspect = bbox_current["x_max"] / bbox_current["y_max"] if bbox_current["y_max"] > 0 else 1.0
                current_width = bbox_current["x_max"]
                current_height = bbox_current["y_max"]
                
                # If layout is too tall (aspect < 0.8), STRONGLY force horizontal expansion
                if current_aspect < 0.8:
                    # Clear most candidates and focus on widening
                    max_x = max(env["x_max"] for pb in placed_blocks for env in pb["envelope"].values())
                    candidates = [0.0, snap_to_grid(max_x), snap_to_grid(max_x + block_w)]
                    # Also try positions that double the width
                    target_width = current_height * 0.9  # Target more square
                    if target_width > current_width:
                        candidates.append(snap_to_grid(target_width - block_w))
                
                # If layout is too wide (aspect > 1.3), prefer stacking
                elif current_aspect > 1.3:
                    # Prefer stacking by using low x values
                    candidates = [0.0] + [c for c in candidates if c < current_width * 0.4]
            
            # Remove duplicates and sort
            candidates = sorted(set(candidates))
            if not candidates:
                candidates = [0.0]
            
            best_x, best_y = 0.0, 0.0
            best_score = float('inf')
            
            for x_cand in candidates:
                # Find initial y position
                y_initial = apply_vertical_gravity(
                    placed_blocks, device_type, envelope, x_cand
                )
                
                # Apply gravity (drop and slide)
                x_final, y_final = apply_gravity(
                    placed_blocks, device_type, envelope, x_cand, y_initial
                )
                
                # Create test block at this position
                test_block = {
                    "main_bbox": {
                        "x_min": x_final,
                        "y_min": y_final,
                        "x_max": x_final + block_w,
                        "y_max": y_final + block_h
                    },
                    "envelope": {
                        etype: {
                            "x_min": x_final + edata["x_min"],
                            "y_min": y_final + edata["y_min"],
                            "x_max": x_final + edata["x_max"],
                            "y_max": y_final + edata["y_max"]
                        }
                        for etype, edata in spacing_envelopes.items()
                    }
                }
                
                # Evaluate this position
                score = evaluate_position(placed_blocks, test_block)
                
                if score < best_score:
                    best_score = score
                    best_x = x_final
                    best_y = y_final
        
        # Place block at best position
        placed_block = {
            "block_id": block["block_id"],
            "device_type": device_type,
            "position": {"x": best_x, "y": best_y},
            "main_bbox": {
                "x_min": best_x,
                "y_min": best_y,
                "x_max": best_x + block_w,
                "y_max": best_y + block_h
            },
            "envelope": {
                etype: {
                    "x_min": best_x + edata["x_min"],
                    "y_min": best_y + edata["y_min"],
                    "x_max": best_x + edata["x_max"],
                    "y_max": best_y + edata["y_max"]
                }
                for etype, edata in spacing_envelopes.items()
            }
        }
        
        placed_blocks.append(placed_block)
    
    return placed_blocks


def calculate_hpwl(netlist, placed_blocks):
    """Calculate Half-Perimeter Wire Length"""
    pin_locs = {}
    
    for block in placed_blocks:
        bid = block["block_id"]
        bbox = block["main_bbox"]
        cx = (bbox["x_min"] + bbox["x_max"]) / 2.0
        cy = (bbox["y_min"] + bbox["y_max"]) / 2.0
        
        for net in netlist["nets"]:
            for pin in net["pins"]:
                if pin.startswith(f"B{bid}_"):
                    pin_locs[pin] = (cx, cy)
    
    total = 0.0
    for net in netlist["nets"]:
        if len(net["pins"]) < 2:
            continue
        
        xs, ys = [], []
        for pin in net["pins"]:
            if pin in pin_locs:
                x, y = pin_locs[pin]
                xs.append(x)
                ys.append(y)
        
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    
    return total


def evaluate_placement(blocks_data, placed_blocks):
    """Calculate placement quality metrics"""
    bbox = calculate_bbox(placed_blocks)
    area = bbox["x_max"] * bbox["y_max"]
    wirelength = calculate_hpwl(blocks_data["netlist"], placed_blocks)
    aspect_ratio = bbox["x_max"] / bbox["y_max"] if bbox["y_max"] > 0 else 1.0
    
    cost = wmi_calculate_cost(
        area=area,
        wirelength=wirelength,
        aspect_ratio=aspect_ratio,
        init_area=1.0,
        init_wirelength=1.0,
        target_ar=1.0,
        weights=(0.4, 0.4, 0.2)
    )
    
    return {
        "area": round(area, 6),
        "wirelength": round(wirelength, 6),
        "aspect_ratio": round(aspect_ratio, 6),
        "bounding_box": bbox,
        "weights": [0.4, 0.4, 0.2],
        "target_aspect_ratio": 1.0,
        "cost": round(cost, 6)
    }


def process_placement(json_data):
    """Main processing function"""
    result = copy.deepcopy(json_data)
    placed_blocks = place_blocks(result)
    cost_function = evaluate_placement(result, placed_blocks)
    
    result["placement"] = {
        "method": "gravity_based",
        "grid_size": GRID_SIZE,
        "placed_blocks": placed_blocks
    }
    result["cost_function"] = cost_function
    
    return result


def process_n8n_input(json_data):
    """Process for n8n (handles both single dict and list)"""
    # Handle list input (from n8n batch)
    if isinstance(json_data, list):
        if len(json_data) > 0:
            result = process_placement(json_data[0])
        else:
            result = {"error": "Empty input list"}
    else:
        result = process_placement(json_data)
    
    return json.loads(json.dumps(result, ensure_ascii=False))


def main_standalone(input_file):
    """Standalone mode for local testing"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Handle list or dict
    if isinstance(json_data, list):
        if len(json_data) > 0:
            data_to_process = json_data[0]
        else:
            print("Error: Empty input list")
            sys.exit(1)
    else:
        data_to_process = json_data
    
    result = process_placement(data_to_process)
    
    # Output file
    output_file = Path.cwd() / f"{input_path.stem}_placed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Placement completed!")
    print(f"  Output: {output_file}")
    print(f"  Area: {result['cost_function']['area']:.2f}")
    print(f"  Wirelength: {result['cost_function']['wirelength']:.2f}")
    print(f"  Aspect ratio: {result['cost_function']['aspect_ratio']:.3f}")
    print(f"  Cost: {result['cost_function']['cost']:.2f}")
    
    # Calculate dead space percentage
    total_block_area = sum(
        (b["main_bbox"]["x_max"] - b["main_bbox"]["x_min"]) *
        (b["main_bbox"]["y_max"] - b["main_bbox"]["y_min"])
        for b in result["placement"]["placed_blocks"]
    )
    dead_space_pct = (1 - total_block_area / result['cost_function']['area']) * 100
    print(f"  Dead space: {dead_space_pct:.1f}%")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        # Standalone mode
        main_standalone(sys.argv[1])
    elif len(sys.argv) == 1:
        # n8n mode
        n8n_processor = create_n8n_processor(process_n8n_input)
        n8n_processor()
    else:
        print("Usage:")
        print("  Standalone: python3 03_initial_placer_improved.py <input_json_file>")
        print("  n8n mode: cat input.json | python3 03_initial_placer_improved.py")
        sys.exit(1)