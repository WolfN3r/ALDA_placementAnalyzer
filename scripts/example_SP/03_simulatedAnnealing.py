#!/usr/bin/env python3
"""
Sequence-Pair Simulated Annealing Optimizer
- Reads JSON from n8n (via n8n_json_handler)
- Optimizes sequence pair + block variants
- Returns best placement + telemetry
"""

import math
import random
import json
from n8n_json_handler import create_n8n_processor

# SA SETTINGS
INITIAL_TEMP = 1000.0
FINAL_TEMP = 0.01
COOLING_RATE = 0.999                    # Slower cooling = more iterations
MAX_ITERATIONS = 50000                  # Much higher limit

# COST FUNCTION WEIGHTS
AREA_WEIGHT = 10.0
DEAD_SPACE_WEIGHT = 1000.0
ASPECT_WEIGHT = 1000.0                  # High penalty for aspect ratio violations
TARGET_ASPECT_RATIO = 1.0
MAX_ASPECT_RATIO = 1.5                  # New: Maximum allowed aspect ratio


def extract_variants(json_data):
    """Get variants per block: {name: [ {width,height}, ... ]}"""
    variants = {}
    for block in json_data.get("blocks", []):
        name = block.get("name")
        if not name:
            continue
        vs = []
        for v in block.get("variants", []):
            try:
                vs.append({
                    "width": float(v["width"]),
                    "height": float(v["height"])
                })
            except Exception:
                continue
        if vs:
            variants[name] = vs
    return variants


def initial_sequence_pair(block_names, json_data):
    """Use existing SP if present, otherwise simple deterministic one."""
    sp = json_data.get("sequence_pair", {})
    r_plus = sp.get("r_plus")
    r_minus = sp.get("r_minus")
    if r_plus and r_minus and len(r_plus) == len(block_names):
        return list(r_plus), list(r_minus)

    names = sorted(block_names)
    return names, list(reversed(names))


def initial_variant_indices(variants, json_data):
    """Prefer default variants from blocks if present, else index 0."""
    default_idx = {name: 0 for name in variants}
    for block in json_data.get("blocks", []):
        name = block.get("name")
        if name not in variants:
            continue
        for i, v in enumerate(block.get("variants", [])):
            if v.get("is_default"):
                default_idx[name] = min(i, len(variants[name]) - 1)
                break
    return default_idx


def decode_sequence_pair(r_plus, r_minus, variants, var_idx):
    """
    Constraint graph method - eliminates dead space.
    """
    if not r_plus:
        return {}

    pos_plus = {block: i for i, block in enumerate(r_plus)}
    pos_minus = {block: i for i, block in enumerate(r_minus)}

    dims = {}
    for block in r_plus:
        v = variants[block][var_idx[block]]
        dims[block] = {"width": v["width"], "height": v["height"]}

    # X coordinates (horizontal constraints)
    x_coords = {}
    for block in r_plus:
        x = 0.0
        for other in r_plus:
            if other != block:
                # other is LEFT of block
                if pos_plus[other] < pos_plus[block] and pos_minus[other] < pos_minus[block]:
                    x = max(x, x_coords.get(other, 0.0) + dims[other]["width"])
        x_coords[block] = x

    # Y coordinates (vertical constraints)
    y_coords = {}
    for block in r_plus:
        y = 0.0
        for other in r_plus:
            if other != block:
                # other is BELOW block
                if pos_plus[other] < pos_plus[block] and pos_minus[other] > pos_minus[block]:
                    y = max(y, y_coords.get(other, 0.0) + dims[other]["height"])
        y_coords[block] = y

    placement = {}
    for block in r_plus:
        x = x_coords[block]
        y = y_coords[block]
        w = dims[block]["width"]
        h = dims[block]["height"]

        placement[block] = {
            "x_min": x,
            "y_min": y,
            "width": w,
            "height": h,
            "x_max": x + w,
            "y_max": y + h
        }

    return placement


def evaluate_placement(placement):
    """Compute fitness with aspect ratio constraint."""
    if not placement:
        return float("inf"), {}, {}

    used_area = 0.0
    max_x = 0.0
    max_y = 0.0

    for p in placement.values():
        used_area += p["width"] * p["height"]
        max_x = max(max_x, p["x_max"])
        max_y = max(max_y, p["y_max"])

    total_area = max_x * max_y if max_x > 0 and max_y > 0 else 0.0
    dead_space = max(total_area - used_area, 0.0)
    dead_space_ratio = (dead_space / total_area * 100.0) if total_area > 0 else 0.0
    aspect_ratio = (max(max_x,max_y)/min(max_x,max_y)) if min(max_x,max_y) > 0 else 0.0

    # Aspect ratio penalty
    aspect_penalty = 0.0
    if aspect_ratio > MAX_ASPECT_RATIO:
        # Heavy penalty for exceeding max aspect ratio
        aspect_penalty = ASPECT_WEIGHT * 1000.0 * (aspect_ratio - MAX_ASPECT_RATIO)
    else:
        # Normal penalty for deviation from target
        aspect_penalty = ASPECT_WEIGHT * abs(aspect_ratio - TARGET_ASPECT_RATIO)

    fitness = (
            AREA_WEIGHT * total_area +
            DEAD_SPACE_WEIGHT * dead_space_ratio +
            aspect_penalty
    )

    metrics = {
        "total_area": total_area,
        "used_area": used_area,
        "dead_space": dead_space,
        "dead_space_percentage": dead_space_ratio,
        "aspect_ratio": aspect_ratio,
        "placement_width": max_x,
        "placement_height": max_y,
        "aspect_ratio_valid": aspect_ratio <= MAX_ASPECT_RATIO
    }

    return fitness, metrics, {"max_x": max_x, "max_y": max_y}


def random_neighbor_state(r_plus, r_minus, var_idx, variants):
    """Generate neighbor by swapping in SP or changing variant."""
    new_rp = list(r_plus)
    new_rm = list(r_minus)
    new_var_idx = dict(var_idx)

    move_type = random.randint(0, 2)

    if move_type == 0 and len(new_rp) > 1:
        i, j = random.sample(range(len(new_rp)), 2)
        new_rp[i], new_rp[j] = new_rp[j], new_rp[i]
    elif move_type == 1 and len(new_rm) > 1:
        i, j = random.sample(range(len(new_rm)), 2)
        new_rm[i], new_rm[j] = new_rm[j], new_rm[i]
    else:
        name = random.choice(list(variants.keys()))
        n_var = len(variants[name])
        if n_var > 1:
            old = new_var_idx.get(name, 0)
            choices = [k for k in range(n_var) if k != old]
            if choices:
                new_var_idx[name] = random.choice(choices)

    return new_rp, new_rm, new_var_idx


def sa_optimize(json_data):
    """Main optimization entry for n8n."""
    variants = extract_variants(json_data)
    if not variants:
        return {"error": "No block variants found", "success": False}

    block_names = list(variants.keys())
    r_plus, r_minus = initial_sequence_pair(block_names, json_data)
    var_idx = initial_variant_indices(variants, json_data)

    placement = decode_sequence_pair(r_plus, r_minus, variants, var_idx)
    cur_fit, cur_metrics, _ = evaluate_placement(placement)

    best_rp = list(r_plus)
    best_rm = list(r_minus)
    best_var_idx = dict(var_idx)
    best_fit = cur_fit
    best_metrics = cur_metrics
    best_placement = placement

    T = INITIAL_TEMP
    iterations = 0
    accepted_moves = 0

    while T > FINAL_TEMP and iterations < MAX_ITERATIONS:
        rpn, rmn, vin = random_neighbor_state(r_plus, r_minus, var_idx, variants)
        pl_n = decode_sequence_pair(rpn, rmn, variants, vin)
        fit_n, met_n, _ = evaluate_placement(pl_n)

        delta = fit_n - cur_fit
        accept = delta < 0 or (T > 0 and random.random() < math.exp(-delta / T))

        if accept:
            r_plus, r_minus, var_idx = rpn, rmn, vin
            cur_fit, cur_metrics = fit_n, met_n
            placement = pl_n
            accepted_moves += 1

            if fit_n < best_fit:
                best_fit = fit_n
                best_metrics = met_n
                best_rp = list(rpn)
                best_rm = list(rmn)
                best_var_idx = dict(vin)
                best_placement = pl_n

        iterations += 1
        T *= COOLING_RATE

    # Build UTF-8 safe output
    placement_out = {}
    for name, p in best_placement.items():
        placement_out[name] = {
            "x_min": round(p["x_min"], 2),
            "y_min": round(p["y_min"], 2),
            "x_max": round(p["x_max"], 2),
            "y_max": round(p["y_max"], 2),
            "width": round(p["width"], 2),
            "height": round(p["height"], 2)
        }

    result = dict(json_data)
    result["sequence_pair"] = {
        "r_plus": best_rp,
        "r_minus": best_rm,
        "placement": placement_out
    }

    result["optimization_results"] = {
        "fitness_function": round(best_fit, 2),
        "total_area": round(best_metrics["total_area"], 2),
        "used_area": round(best_metrics["used_area"], 2),
        "dead_space": round(best_metrics["dead_space"], 2),
        "dead_space_percentage": round(best_metrics["dead_space_percentage"], 2),
        "aspect_ratio": round(best_metrics["aspect_ratio"], 2),
        "aspect_ratio_valid": best_metrics["aspect_ratio_valid"],
        "max_aspect_ratio": MAX_ASPECT_RATIO,
        "placement_width": round(best_metrics["placement_width"], 2),
        "placement_height": round(best_metrics["placement_height"], 2),
        "actual_iterations": iterations,
        "accepted_moves": accepted_moves,
        "acceptance_rate": round(accepted_moves / iterations * 100, 2) if iterations > 0 else 0,
        "optimization_method": "simulated_annealing_sequence_pair"
    }

    # Ensure UTF-8 encoding
    return json.loads(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    processor = create_n8n_processor(sa_optimize)
    processor()