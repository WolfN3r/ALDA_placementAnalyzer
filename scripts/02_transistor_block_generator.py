#!/usr/bin/env python3
"""
Transistor Block Generator
Generates random transistor blocks based on technology constraints
Works with n8n or standalone
"""

import json
import random
import sys
import os
from pathlib import Path

# Import n8n handler from lib directory
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor


def snap_to_grid(value, grid):
    """Round value to manufacturing grid"""
    return round(round(value / grid) * grid, 6)


def snap_to_step(value, step):
    """Round value to specified step (for W/L generation)"""
    return round(round(value / step) * step, 6)


def wmi_generate_transistor_block(tech_file, width, length, multiplier, num_fingers,
                               min_aspect_ratio, max_aspect_ratio, device_type):
    """Generate all valid transistor block variants with spacing envelopes"""
    
    # Get manufacturing grid
    grid = tech_file["technology_info"]["manufacturing_grid"]
    
    # W and L are already snapped to step during generation, no need to re-snap here
    
    # Validate inputs
    device = tech_file["device_constraints"][device_type]
    assert device["L"]["min"] <= length <= device["L"]["max"], f"Length {length} out of range"
    assert device["W"]["min"] <= width <= device["W"]["max"], f"Width {width} out of range"
    assert multiplier >= 1, "Multiplier must be >= 1"
    assert num_fingers >= 1, "num_fingers must be >= 1"
    
    # Extract design rules
    rules = tech_file["physical_design_rules"]
    poly_width = rules["poly"]["min_width"]
    poly_spacing = rules["poly"]["min_spacing"]
    poly_ext_active = rules["poly"]["extension_over_active"]
    active_ext_poly = rules["active"]["extension_past_poly"]
    active_spacing = rules["active"]["min_spacing"]
    contact_size = rules["contact"]["size"]
    contact_enclosure = rules["contact"]["enclosure_by_active"]
    
    # Calculate single finger dimensions
    w_finger = width / num_fingers
    finger_width_with_contacts = w_finger + 2 * (contact_enclosure + contact_size)
    finger_pitch = finger_width_with_contacts + poly_width + poly_spacing
    
    active_height = w_finger
    
    # Generate all possible variants
    total_fingers = multiplier * num_fingers
    variants = []
    
    for n_rows in range(1, total_fingers + 1):
        if total_fingers % n_rows == 0:
            n_cols = total_fingers // n_rows
            
            # Calculate block dimensions
            block_width = n_cols * finger_pitch - poly_spacing
            block_height = n_rows * (active_height + active_spacing) - active_spacing
            
            # Snap to grid
            block_width = snap_to_grid(block_width, grid)
            block_height = snap_to_grid(block_height, grid)
            
            # Calculate aspect ratio (width/height)
            aspect_ratio = block_width / block_height if block_height > 0 else 0
            
            # Filter by aspect ratio
            if min_aspect_ratio <= aspect_ratio <= max_aspect_ratio:
                # Create arrangement structure
                arrangement = []
                finger_idx = 0
                for row in range(n_rows):
                    row_fingers = []
                    for col in range(n_cols):
                        row_fingers.append(finger_idx)
                        finger_idx += 1
                    arrangement.append(row_fingers)
                
                # Generate matching scheme (symmetrical pairing)
                matching_pairs = []
                if multiplier >= 2:
                    for i in range(multiplier // 2):
                        matching_pairs.append([i, multiplier - 1 - i])
                
                # Create main bounding box
                main_bbox = {
                    "x_min": 0.0,
                    "y_min": 0.0,
                    "x_max": snap_to_grid(block_width, grid),
                    "y_max": snap_to_grid(block_height, grid)
                }
                
                # Generate spacing envelopes
                spacing_matrix = tech_file["inter_device_spacing_matrix"]
                spacing_envelopes = {}
                
                for neighbor_type in ["nmos1v_nat", "nmos2v_nat", "pmos1v_nat", "pmos2v_nat"]:
                    spacing = spacing_matrix[device_type][neighbor_type]
                    spacing_envelopes[neighbor_type] = {
                        "x_min": snap_to_grid(0.0 - spacing, grid),
                        "y_min": snap_to_grid(0.0 - spacing, grid),
                        "x_max": snap_to_grid(block_width + spacing, grid),
                        "y_max": snap_to_grid(block_height + spacing, grid)
                    }
                
                variants.append({
                    "layout": {
                        "rows": n_rows,
                        "cols": n_cols,
                        "aspect_ratio": round(aspect_ratio, 3),
                        "arrangement": arrangement
                    },
                    "matching_scheme": matching_pairs,
                    "main_bbox": main_bbox,
                    "spacing_envelopes": spacing_envelopes,
                    "is_used": False
                })
    
    # Construct final output
    return {
        "device_type": device_type,
        "parameters": {
            "width": width,
            "length": length,
            "multiplier": multiplier,
            "num_fingers": num_fingers,
            "total_fingers": total_fingers
        },
        "variants": variants
    }


def wmi_generate_netlist(blocks, config, seed):
    """
    Generate netlist with clustered connections
    """
    random.seed(seed)
    
    netlist_config = config["netlist"]
    density = netlist_config["density"]
    pins_min = netlist_config["pins_per_block_min"]
    pins_max = netlist_config["pins_per_block_max"]
    
    valid_blocks = [b for b in blocks if 'error' not in b]
    num_blocks = len(valid_blocks)
    target_nets = max(2, int(density * num_blocks))
    
    # Step 1: Create all pins
    all_pins = []
    for block in valid_blocks:
        block_idx = block['block_id']
        num_pins = random.randint(pins_min, pins_max)
        for pin_idx in range(num_pins):
            all_pins.append({
                "block_id": block_idx,
                "pin_name": f"B{block_idx}_P{pin_idx}"
            })
    
    random.shuffle(all_pins)
    used_pins = set()
    nets = []
    
    # Step 2: Create nets until target reached
    while len(nets) < target_nets and len(all_pins) > len(used_pins):
        # Get unused pins
        available = [p for p in all_pins if p["pin_name"] not in used_pins]
        if len(available) < 2:
            break
        
        # Create cluster with 2-4 pins from different blocks
        cluster_size = min(random.randint(2, 4), len(available))
        cluster = []
        blocks_used = set()
        
        for pin in available:
            if len(cluster) >= cluster_size:
                break
            # Add pin if from different block or if we need more pins
            if pin["block_id"] not in blocks_used or len(cluster) == 0:
                cluster.append(pin)
                blocks_used.add(pin["block_id"])
        
        # Only create net if we have pins from at least 2 blocks
        if len(blocks_used) >= 2:
            net_pins = [p["pin_name"] for p in cluster]
            nets.append({
                "net_id": f"net_{len(nets)}",
                "pins": net_pins
            })
            for p in cluster:
                used_pins.add(p["pin_name"])
        else:
            # Mark these pins as used to avoid infinite loop
            for p in cluster:
                used_pins.add(p["pin_name"])
    
    # Step 3: Distribute remaining pins
    remaining = [p for p in all_pins if p["pin_name"] not in used_pins]
    for pin in remaining:
        if nets:
            target_net = random.choice(nets)
            target_net["pins"].append(pin["pin_name"])
    
    netlist = {
        "num_nets": len(nets),
        "num_pins": len(all_pins),
        "density": round(len(nets) / num_blocks, 2) if num_blocks > 0 else 0,
        "nets": nets
    }
    
    return netlist


def wmi_generate_random_blocks(tech_file, config, num_of_blocks, seed):
    """Generate multiple random transistor blocks"""
    random.seed(seed)
    
    device_types = ["nmos1v_nat", "nmos2v_nat", "pmos1v_nat", "pmos2v_nat"]
    max_attempts = config["validation"]["max_generation_attempts"]
    
    # Extract configuration parameters
    gen_params = config["generation_params"]
    length_step = gen_params["length_range"]["step"]
    width_step = gen_params["width_range"]["step"]
    multiplier_min = gen_params["multiplier_range"]["min"]
    multiplier_max = gen_params["multiplier_range"]["max"]
    nf_min = gen_params["num_fingers_range"]["min"]
    nf_max = gen_params["num_fingers_range"]["max"]
    
    aspect_config = gen_params["aspect_ratio"]
    min_aspect_min = aspect_config["min_aspect_min"]
    min_aspect_max = aspect_config["min_aspect_max"]
    max_aspect_min = aspect_config["max_aspect_min"]
    max_aspect_max = aspect_config["max_aspect_max"]
    
    # Get design constraints
    design_constraints = config["design_constraints"]
    
    blocks = []
    
    for i in range(num_of_blocks):
        block = None
        
        # Try to generate a block with at least one variant
        for attempt in range(max_attempts):
            try:
                # Randomly select device type
                device_type = random.choice(device_types)
                device = tech_file["device_constraints"][device_type]
                
                # Get design constraints for this device type
                design_device = design_constraints[device_type]
                
                # Generate random parameters within design constraints, snap to step
                length_min = design_device["L"]["min"]
                length_max = design_device["L"]["max"]
                length = snap_to_step(random.uniform(length_min, length_max), length_step)
                
                width_min = design_device["W"]["min"]
                width_max = design_device["W"]["max"]
                width = snap_to_step(random.uniform(width_min, width_max), width_step)
                
                # Generate even multiplier
                multiplier = random.randrange(multiplier_min, multiplier_max + 1, 2)
                if multiplier < multiplier_min:
                    multiplier = multiplier_min
                
                num_fingers = random.randint(nf_min, nf_max)
                
                # Random aspect ratio constraints
                min_aspect = round(random.uniform(min_aspect_min, min_aspect_max), 2)
                max_aspect = round(random.uniform(max_aspect_min, max_aspect_max), 2)
                
                # Generate block
                test_block = wmi_generate_transistor_block(
                    tech_file, width, length, multiplier, num_fingers,
                    min_aspect, max_aspect, device_type
                )
                
                # Check if at least one variant was generated
                if len(test_block["variants"]) > 0:
                    test_block["block_id"] = i
                    test_block["generation_attempts"] = attempt + 1
                    block = test_block
                    break
                    
            except Exception as e:
                # Continue trying
                if attempt == max_attempts - 1:
                    # Last attempt failed, record error
                    block = {
                        "block_id": i,
                        "error": str(e),
                        "generation_attempts": max_attempts,
                        "parameters": {
                            "device_type": device_type,
                            "width": width,
                            "length": length,
                            "multiplier": multiplier,
                            "num_fingers": num_fingers
                        }
                    }
        
        if block is None:
            # Failed to generate valid block
            block = {
                "block_id": i,
                "error": "Failed to generate block with valid variants",
                "generation_attempts": max_attempts
            }
        
        blocks.append(block)
    
    # Generate netlist
    netlist = wmi_generate_netlist(blocks, config, seed)
    
    return {
        "generation_params": {
            "num_of_blocks": num_of_blocks,
            "seed": seed
        },
        "technology": tech_file["technology_info"]["name"],
        "blocks": blocks,
        "netlist": netlist
    }


def process_n8n_input(json_data):
    """Process input from n8n"""
    script_dir = Path(__file__).parent
    config_path = script_dir / "lib" / "generation_config.json"
    
    # Load configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    tech_file = {
        "technology_info": json_data["technology_info"],
        "device_constraints": json_data["device_constraints"],
        "physical_design_rules": json_data["physical_design_rules"],
        "inter_device_spacing_matrix": json_data["inter_device_spacing_matrix"]
    }
    
    gen_params = json_data["gen_params"]
    num_of_blocks = gen_params["num_of_blocks"]
    seed = gen_params["seed"]
    
    assert num_of_blocks > 0, "num_of_blocks must be positive"
    
    result = wmi_generate_random_blocks(tech_file, config, num_of_blocks, seed)
    
    # Ensure UTF-8 safe output
    return json.loads(json.dumps(result, ensure_ascii=False))


def main_standalone(num_of_blocks, seed):
    """Run standalone with tech file from lib directory"""
    script_dir = Path(__file__).parent
    lib_dir = script_dir / "lib"
    tech_file_path = lib_dir / "gpdk090_tech_simple.json"
    config_path = lib_dir / "generation_config.json"
    
    # Load technology file
    with open(tech_file_path, 'r', encoding='utf-8') as f:
        tech_file = json.load(f)
    
    # Load configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    result = wmi_generate_random_blocks(tech_file, config, num_of_blocks, seed)
    
    # Save to json_files directory
    output_dir = script_dir / "json_files"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"blocks_seed{seed}_n{num_of_blocks}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Standalone mode with arguments
        try:
            num_of_blocks = int(sys.argv[1])
            seed = int(sys.argv[2])
            if num_of_blocks <= 0:
                print("Error: num_of_blocks must be positive")
                sys.exit(1)
            main_standalone(num_of_blocks, seed)
        except ValueError:
            print("Usage: python3 transistor_block_generator.py <num_of_blocks> <seed>")
            print("Example: python3 transistor_block_generator.py 5 42")
            sys.exit(1)
    elif len(sys.argv) == 1:
        # n8n mode (no arguments)
        n8n_processor = create_n8n_processor(process_n8n_input)
        n8n_processor()
    else:
        print("Usage:")
        print("  Standalone: python3 transistor_block_generator.py <num_of_blocks> <seed>")
        print("  n8n mode: cat input.json | python3 transistor_block_generator.py")
        sys.exit(1)