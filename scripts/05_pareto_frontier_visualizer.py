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

# Import n8n handler
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor


def generate_colors(n):
    """Generate distinct colors"""
    cmap = plt.cm.get_cmap('tab20')
    return [cmap(i / n) for i in range(n)]


def process_pareto_data(json_data):
    """Process and visualize Pareto frontier"""
    
    try:
        if not json_data:
            return {"error": "Empty input"}
        
        # Simple approach like 04_initial_placement_visualizer
        # Expect list of data points directly
        if isinstance(json_data, list):
            data_points = json_data
        else:
            data_points = [json_data]
        
        if not data_points:
            return {"error": "No data points"}
        
        # Extract info
        seeds = []
        areas = []
        wirelengths = []
        costs = []
        aspect_ratios = []
        
        for point in data_points:
            gen_params = point.get('generation_params', {})
            cost_func = point.get('cost_function', {})
            
            seeds.append(gen_params.get('seed', 0))
            areas.append(cost_func.get('area', 0))
            wirelengths.append(cost_func.get('wirelength', 0))
            costs.append(cost_func.get('cost', 0))
            aspect_ratios.append(cost_func.get('aspect_ratio', 0))
        
        num_blocks = data_points[0].get('generation_params', {}).get('num_of_blocks', 0)
        colors = generate_colors(len(seeds))
        
        # Create figure
        fig = plt.figure(figsize=(16, 8))
        ax1 = plt.subplot(121)  # Left: Pareto plot
        ax2 = plt.subplot(122)  # Right: Table
        
        fig.suptitle('Pareto Frontier Analysis', fontsize=16, fontweight='bold')
        
        # ===== LEFT: Pareto Frontier =====
        ax1.set_title('Area vs Wirelength Trade-off', fontsize=14)
        ax1.set_xlabel('Area', fontsize=12)
        ax1.set_ylabel('Wirelength', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Plot points
        for i, (area, wl, seed, color) in enumerate(zip(areas, wirelengths, seeds, colors)):
            ax1.scatter(area, wl, s=200, c=[color], edgecolors='black', 
                       linewidth=2, label=f'Seed {seed}', zorder=3)
        
        ax1.legend(loc='best', fontsize=9)
        
        # ===== RIGHT: Results Table =====
        ax2.axis('off')
        ax2.set_title('Results Summary', fontsize=14, fontweight='bold', pad=20)
        
        # Build table data
        table_data = [['Seed', 'Cost', 'Area', 'Wirelength', 'Aspect Ratio']]
        
        for seed, cost, area, wl, ar in zip(seeds, costs, areas, wirelengths, aspect_ratios):
            table_data.append([
                str(seed),
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
            colWidths=[0.1, 0.15, 0.15, 0.15, 0.15]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header
        for i in range(5):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.tight_layout()
        
        # Prepare output data
        output_data = []
        for seed, cost, area, wl, ar in zip(seeds, costs, areas, wirelengths, aspect_ratios):
            output_data.append({
                "seed": seed,
                "cost": cost,
                "area": area,
                "wirelength": wl,
                "aspect_ratio": ar
            })
        
        # Display or save
        if DISPLAY_MODE == 1:
            plt.show()
            return {"results": output_data}
        else:
            script_dir = Path(__file__).parent
            output_dir = script_dir / 'pareto_frontier'
            output_dir.mkdir(exist_ok=True)
            
            first_seed = seeds[0] if seeds else 0
            output_path = output_dir / f'pareto_frontier_seed{first_seed}_n{num_blocks}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return {
                "visualization_saved": str(output_path),
                "results": output_data
            }
        
    except Exception as e:
        return {"error": str(e)}


def process_n8n_input(json_data):
    """Process input from n8n"""
    result = process_pareto_data(json_data)
    return json.loads(json.dumps(result, ensure_ascii=False))


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