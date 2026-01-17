#!/usr/bin/env python3
"""
Pareto Frontier Visualizer - Multi-objective optimization analysis
Shows area vs wirelength trade-offs across different seeds
"""

import sys
import json
from pathlib import Path

# Configuration
DISPLAY_MODE = 0  # 0 = save PNG, 1 = show with Xming

# Set matplotlib backend
import matplotlib
if DISPLAY_MODE == 1:
    matplotlib.use('TkAgg')
else:
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import gc
import warnings

# Suppress matplotlib layout warnings for large datasets
warnings.filterwarnings('ignore', message='Tight layout not applied')

# Import n8n handler
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor


def is_pareto_efficient(costs):
    """
    Find the pareto-efficient points
    costs: An (n_points, n_costs) array
    returns: A boolean array of whether each point is Pareto efficient
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        if is_efficient[i]:
            # Keep points that are not dominated by point i
            # Point j dominates point i if all costs of j <= costs of i and at least one cost is strictly less
            is_efficient[is_efficient] = np.any(costs[is_efficient] < c, axis=1) | np.all(costs[is_efficient] == c, axis=1)
            is_efficient[i] = True  # Keep self
    return is_efficient


def generate_colors(n):
    """Generate distinct colors"""
    if n <= 20:
        cmap = plt.colormaps.get_cmap('tab20')
    else:
        cmap = plt.colormaps.get_cmap('hsv')
    return [cmap(i / max(n, 1)) for i in range(n)]



def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

def process_pareto_data(json_data):
    """Process and visualize Pareto frontier"""
    
    try:
        if not json_data:
            return {"error": "Empty input", "success": False}
        
        # Handle input - expect list of data points
        if isinstance(json_data, list):
            data_points = json_data
        else:
            data_points = [json_data]
        
        if not data_points:
            return {"error": "No data points", "success": False}
        
        # Memory safety check for very large datasets
        if len(data_points) > 100:
            return {
                "success": False,
                "error": f"Dataset too large ({len(data_points)} points). Maximum supported: 100 points.",
                "hint": "Consider processing data in smaller batches or reducing repetitions."
            }
        
        # Extract metrics
        seeds = []
        areas = []
        wirelengths = []
        costs = []
        aspect_ratios = []
        
        for point in data_points:
            # Validate structure
            if not isinstance(point, dict):
                continue
                
            gen_params = point.get('generation_params', {})
            cost_func = point.get('cost_function', {})
            
            # Extract with validation
            seed = gen_params.get('seed', 0)
            area = cost_func.get('area', 0)
            wl = cost_func.get('wirelength', 0)
            cost = cost_func.get('cost', 0)
            ar = cost_func.get('aspect_ratio', 0)
            
            # Only add if we have valid data
            if area > 0 or wl > 0:
                seeds.append(seed)
                areas.append(area)
                wirelengths.append(wl)
                costs.append(cost)
                aspect_ratios.append(ar)
        
        if not seeds:
            return {"error": "No valid data extracted", "success": False}
        
        # Get number of blocks from first point
        num_blocks = data_points[0].get('generation_params', {}).get('num_of_blocks', 0)
        
        # Find Pareto frontier
        # For minimization: lower area AND lower wirelength is better
        objective_costs = np.column_stack([areas, wirelengths])
        pareto_mask = is_pareto_efficient(objective_costs)
        
        # Generate colors
        colors = generate_colors(len(seeds))
        
        # Create figure with larger size for better visibility
        # Adaptive figure sizing to reduce memory usage
        if len(seeds) > 30:
            # Large dataset: reduce size and DPI
            fig = plt.figure(figsize=(14, 6))
            save_dpi = 200  # Lower DPI for large datasets
        else:
            # Normal dataset: full quality
            fig = plt.figure(figsize=(18, 8))
            save_dpi = 300
        ax1 = plt.subplot(121)  # Left: Pareto plot
        ax2 = plt.subplot(122)  # Right: Table
        
        fig.suptitle(f'Pareto Frontier Analysis (n={num_blocks} blocks)', 
                     fontsize=14, fontweight='bold')
        
        # ===== LEFT: Pareto Frontier =====
        ax1.set_title('Area vs Wirelength Trade-off', fontsize=12)
        ax1.set_xlabel('Area', fontsize=11)
        ax1.set_ylabel('Wirelength (HPWL)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Plot all points
        for i, (area, wl, seed, color, is_pareto) in enumerate(
            zip(areas, wirelengths, seeds, colors, pareto_mask)):
            
            marker = 'D' if is_pareto else 'o'  # Diamond for Pareto points
            size = 69 if is_pareto else 50
            linewidth = 2 if is_pareto else 1
            zorder = 5 if is_pareto else 3
            
            label = f'Seed {seed}' + (' (Pareto)' if is_pareto else '')
            
            ax1.scatter(area, wl, s=size, c=[color], marker=marker,
                       edgecolors='black', linewidth=linewidth, 
                       label=label, zorder=zorder, alpha=0.8)
            
            # Add text label near point
            if len(data_points) <= 30:  # Only label for small datasets
                ax1.annotate(f'{seed}', (area, wl), xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='bold')
        
        # Draw Pareto frontier line
        if np.sum(pareto_mask) > 1:
            pareto_areas = [a for a, p in zip(areas, pareto_mask) if p]
            pareto_wls = [w for w, p in zip(wirelengths, pareto_mask) if p]
            
            # Sort by area for proper line drawing
            sorted_indices = np.argsort(pareto_areas)
            sorted_areas = [pareto_areas[i] for i in sorted_indices]
            sorted_wls = [pareto_wls[i] for i in sorted_indices]
            
            ax1.plot(sorted_areas, sorted_wls, 'r--', 
                    linewidth=2, alpha=0.5, label='Pareto Frontier',
                    zorder=2)
        
        # Only show legend for datasets with <= 16 points
        if len(data_points) <= 16:
            ax1.legend(loc='best', fontsize=9, framealpha=0.9)
        
        # Add some margin to axes
        x_margin = (max(areas) - min(areas)) * 0.1 if len(areas) > 1 else max(areas) * 0.1
        y_margin = (max(wirelengths) - min(wirelengths)) * 0.1 if len(wirelengths) > 1 else max(wirelengths) * 0.1
        
        ax1.set_xlim(min(areas) - x_margin, max(areas) + x_margin)
        ax1.set_ylim(min(wirelengths) - y_margin, max(wirelengths) + y_margin)
        
        # ===== RIGHT: Results Table =====
        ax2.axis('off')
        
        # Create list of tuples for sorting by cost
        data_tuples = list(zip(seeds, costs, areas, wirelengths, aspect_ratios, pareto_mask))
        
        # Sort by cost (lowest first)
        data_tuples.sort(key=lambda x: x[1])  # Sort by cost (index 1)
        
        # Limit to top 16 if more than 16 points
        if len(data_tuples) > 16:
            data_tuples = data_tuples[:16]
            table_title = f'Top 16 Results (by Cost) - {len(seeds)} total'
        else:
            table_title = 'Results Summary (by Cost)'
        
        ax2.set_title(table_title, fontsize=12, fontweight='bold', pad=20)
        
        # Build table data
        table_data = [['Seed', 'Pareto', 'Cost', 'Area', 'Wirelength', 'Aspect Ratio']]
        
        for seed, cost, area, wl, ar, is_pareto in data_tuples:
            pareto_mark = 'Y' if is_pareto else ''
            table_data.append([
                str(seed),
                pareto_mark,
                f'{cost:.4f}',
                f'{area:.2f}',
                f'{wl:.2f}',
                f'{ar:.4f}'
            ])
        
        # Create table
        table = ax2.table(
            cellText=table_data,
            cellLoc='center',
            loc='center',
            colWidths=[0.08, 0.08, 0.15, 0.15, 0.15, 0.15]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(8 if len(data_points) > 30 else 9)
        table.scale(1, 2)
        
        # Style header
        for j in range(6):
            table[(0, j)].set_facecolor('#4CAF50')
            table[(0, j)].set_text_props(weight='bold', color='white')
        
        # Highlight Pareto-efficient rows in the table
        for row_idx, (seed, cost, area, wl, ar, is_pareto) in enumerate(data_tuples, start=1):
            if is_pareto:
                for j in range(6):
                    table[(row_idx, j)].set_facecolor('#E8F5E9')
        
        
        try:
            plt.tight_layout()
        except:
            pass  # Ignore layout warnings for large datasets
        
        # Prepare output data with immediate type conversion
        output_data = []
        for seed, cost, area, wl, ar, is_pareto in zip(
            seeds, costs, areas, wirelengths, aspect_ratios, pareto_mask):
            output_data.append({
                "seed": int(seed),  # Convert to Python int
                "cost": float(cost),  # Convert to Python float
                "area": float(area),
                "wirelength": float(wl),
                "aspect_ratio": float(ar),
                "is_pareto_efficient": bool(is_pareto)  # Convert numpy.bool_ to Python bool
            })

        # Save values we'll need later before deleting
        num_points = len(seeds)
        num_pareto_points = int(np.sum(pareto_mask))
        first_seed = seeds[0] if seeds else 0
        last_seed = seeds[-1] if seeds else 0
        
        # Immediately delete extracted lists to free memory
        del seeds, costs, areas, wirelengths, aspect_ratios
        gc.collect()
        
        # Display or save
        if DISPLAY_MODE == 1:
            plt.show()
            plt.close()  # Clean up matplotlib resources
            
            # Aggressively clean up matplotlib resources
            del fig, ax1, ax2, table
            del objective_costs, pareto_mask, colors
            gc.collect()
            
            result = {
                "success": True,
                "results": output_data,
                "num_points": num_points,
                "num_pareto_points": num_pareto_points
            }
        else:
            script_dir = Path(__file__).parent
            output_dir = script_dir / 'pareto_frontier'
            output_dir.mkdir(exist_ok=True)
            
            # first_seed and last_seed already saved before deletion
            output_path = output_dir / f'pareto_frontier_seeds{first_seed}-{last_seed}_n{num_blocks}.png'
            
            plt.savefig(output_path, dpi=save_dpi, bbox_inches='tight')
            plt.close()

            # Aggressively clean up matplotlib resources
            del fig, ax1, ax2, table
            del objective_costs, pareto_mask, colors
            gc.collect()
            
            result = {
                "success": True,
                "visualization_saved": str(output_path),
                "results": output_data,
                "num_points": num_points,
                "num_pareto_points": num_pareto_points
            }
        
        # Clean up matplotlib and convert numpy types
        gc.collect()
        return convert_numpy_types(result)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace
        }


def process_n8n_input(json_data):
    """Process input from n8n"""
    result = process_pareto_data(json_data)
    # Return Python dict directly - n8n_json_handler will serialize to JSON
    # Clean up matplotlib and convert numpy types
    gc.collect()
    return convert_numpy_types(result)


def main_standalone(input_file):
    """Run standalone with input file"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    result = process_pareto_data(json_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main_standalone(sys.argv[1])
    elif len(sys.argv) == 1:
        n8n_processor = create_n8n_processor(process_n8n_input)
        n8n_processor()
    else:
        print("Usage:")
        print("  Standalone: python3 05_pareto_frontier_visualizer.py <input.json>")
        print("  n8n mode: cat input.json | python3 05_pareto_frontier_visualizer.py")
        sys.exit(1)