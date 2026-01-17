#!/usr/bin/env python3
"""
Placement Visualizer for n8n - Shows block placement with envelopes and metrics
"""

import sys
import json
import colorsys
from pathlib import Path

# Configuration
DISPLAY_MODE = 0  # 0 = save PNG, 1 = show with Xming

# Device type colors: (fill_color, edge_color, linestyle)
DEVICE_COLORS = {
    "nmos1v_nat": ("#FFB6B6", "#FF4444", "--"),  # Light coral / Red
    "nmos2v_nat": ("#B6FFB6", "#44FF44", "--"),  # Light green / Green
    "pmos1v_nat": ("#B6B6FF", "#4444FF", "--"),  # Light blue / Blue
    "pmos2v_nat": ("#FFB6FF", "#FF44FF", "--")   # Light pink / Magenta
}

# Set matplotlib backend before importing pyplot
import matplotlib
if DISPLAY_MODE == 1:
    matplotlib.use('TkAgg')
else:
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# Import n8n handler from lib directory
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor


def generate_distinct_colors(num_colors):
    """Generate distinct colors using HSV"""
    colors = []
    for i in range(num_colors):
        hue = (i * 0.618033988749895) % 1.0
        saturation = 0.8 + (i % 3) * 0.1
        value = 0.7 + (i % 2) * 0.2
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
    return colors


def process_placement_data(json_data):
    """Process and visualize placement data"""
    
    try:
        if not json_data:
            return {"success": False, "error": "Input JSON data is empty"}
        
        data = json_data[0] if isinstance(json_data, list) else json_data
        
        if 'placement' not in data or 'cost_function' not in data:
            return {"success": False, "error": "Invalid JSON structure"}
        
        placement = data['placement']
        cost_function = data['cost_function']
        netlist = data.get('netlist', {'nets': []})
        placed_blocks = placement['placed_blocks']
        
        # Envelope colors using device type colors
        envelope_colors = {
            'nmos1v_nat': DEVICE_COLORS['nmos1v_nat'][1],
            'nmos2v_nat': DEVICE_COLORS['nmos2v_nat'][1],
            'pmos1v_nat': DEVICE_COLORS['pmos1v_nat'][1],
            'pmos2v_nat': DEVICE_COLORS['pmos2v_nat'][1]
        }
        
        # Net colors
        net_colors = generate_distinct_colors(len(netlist['nets']))
        
        # Calculate shift
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for block in placed_blocks:
            for env_type, env in block['envelope'].items():
                min_x = min(min_x, env['x_min'])
                min_y = min(min_y, env['y_min'])
                max_x = max(max_x, env['x_max'])
                max_y = max(max_y, env['y_max'])
        
        shift_x = -min_x if min_x < 0 else 0
        shift_y = -min_y if min_y < 0 else 0
        
        bbox_x_min = 0.0
        bbox_y_min = 0.0
        bbox_x_max = max_x + shift_x
        bbox_y_max = max_y + shift_y
        
        # Create figure
        fig = plt.figure(figsize=(16, 8))
        ax1 = plt.subplot(121)
        ax2 = plt.subplot(122)
        
        fig.suptitle('Placement Visualization', fontsize=16, fontweight='bold')
        
        # LEFT: Block Placement
        ax1.set_title('Block Placement with Envelopes', fontsize=14)
        ax1.set_aspect('equal')
        ax1.set_xlabel('X', fontsize=12)
        ax1.set_ylabel('Y', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        block_centers = {}
        
        # Draw blocks and envelopes
        for idx, block in enumerate(placed_blocks):
            block_id = block['block_id']
            device_type = block['device_type']
            main_bbox = block['main_bbox']
            envelopes = block['envelope']
            
            # Get device color
            block_color = DEVICE_COLORS[device_type][0]
            
            # Shift coordinates
            main_x_min = main_bbox['x_min'] + shift_x
            main_y_min = main_bbox['y_min'] + shift_y
            main_x_max = main_bbox['x_max'] + shift_x
            main_y_max = main_bbox['y_max'] + shift_y
            
            main_width = main_x_max - main_x_min
            main_height = main_y_max - main_y_min
            
            center_x = main_x_min + main_width / 2
            center_y = main_y_min + main_height / 2
            block_centers[block_id] = (center_x, center_y)
            
            # Draw main block with device type color
            main_rect = Rectangle(
                (main_x_min, main_y_min), 
                main_width, 
                main_height,
                facecolor=block_color,
                edgecolor='black', 
                linewidth=2,
                alpha=0.8,
                zorder=2
            )
            ax1.add_patch(main_rect)
            
            # Add block ID label
            ax1.text(
                center_x, center_y, 
                f'B{block_id}',
                ha='center', va='center', 
                fontweight='bold', 
                fontsize=11,
                zorder=3
            )
            
            # Add device type label below block ID
            ax1.text(
                center_x, center_y - main_height * 0.2, 
                device_type,
                ha='center', va='center', 
                fontsize=6,
                zorder=3
            )
            
            # Draw envelopes
            for env_type, env in envelopes.items():
                env_x_min = env['x_min'] + shift_x
                env_y_min = env['y_min'] + shift_y
                env_x_max = env['x_max'] + shift_x
                env_y_max = env['y_max'] + shift_y
                
                env_width = env_x_max - env_x_min
                env_height = env_y_max - env_y_min
                
                env_rect = Rectangle(
                    (env_x_min, env_y_min),
                    env_width,
                    env_height,
                    facecolor='none',
                    edgecolor=envelope_colors.get(env_type, '#888888'),
                    linewidth=1.5,
                    linestyle='--',
                    alpha=0.7,
                    zorder=1
                )
                ax1.add_patch(env_rect)
        
        # Draw nets
        for net_idx, net in enumerate(netlist['nets']):
            pins = net['pins']
            block_ids = []
            for pin in pins:
                if pin.startswith('B') and '_P' in pin:
                    bid = int(pin.split('_')[0][1:])
                    if bid in block_centers:
                        block_ids.append(bid)
            
            if len(block_ids) >= 2:
                for i in range(len(block_ids)):
                    for j in range(i + 1, len(block_ids)):
                        x1, y1 = block_centers[block_ids[i]]
                        x2, y2 = block_centers[block_ids[j]]
                        ax1.plot(
                            [x1, x2], [y1, y2],
                            color=net_colors[net_idx % len(net_colors)],
                            linewidth=2,
                            alpha=0.6,
                            zorder=0
                        )
        
        # Draw bounding box
        bbox_width = bbox_x_max - bbox_x_min
        bbox_height = bbox_y_max - bbox_y_min
        
        bbox_rect = Rectangle(
            (bbox_x_min, bbox_y_min),
            bbox_width,
            bbox_height,
            facecolor='none',
            edgecolor='red',
            linewidth=3,
            linestyle='-',
            zorder=4
        )
        ax1.add_patch(bbox_rect)
        
        margin = max(bbox_width, bbox_height) * 0.05
        ax1.set_xlim(bbox_x_min - margin, bbox_x_max + margin)
        ax1.set_ylim(bbox_y_min - margin, bbox_y_max + margin)
        
        # Legend
        legend_elements = []
        for env_type, color in envelope_colors.items():
            legend_elements.append(
                Line2D([0], [0], color=color, linewidth=2, linestyle='--', 
                       label=f'{env_type} envelope')
            )
        legend_elements.append(
            Line2D([0], [0], color='red', linewidth=3, linestyle='-', 
                   label='Bounding Box')
        )
        if len(netlist['nets']) > 0:
            legend_elements.append(
                Line2D([0], [0], color='gray', linewidth=2, linestyle='-', 
                       label='Nets', alpha=0.6)
            )
        
        ax1.legend(handles=legend_elements, loc='upper left', fontsize=6)
        
        # RIGHT: Metrics Table
        ax2.axis('off')
        ax2.set_title('Placement Metrics', fontsize=14, fontweight='bold', pad=20)
        
        gen_params = data.get('generation_params', {})
        
        table_data = [
            ['Parameter', 'Value'],
            ['', ''],
            ['Number of Blocks', str(gen_params.get('num_of_blocks', 'N/A'))],
            ['Seed', str(gen_params.get('seed', 'N/A'))],
            ['', ''],
            ['Area', f"{cost_function['area']:.4f}"],
            ['Wirelength (HPWL)', f"{cost_function['wirelength']:.4f}"],
            ['Aspect Ratio', f"{cost_function['aspect_ratio']:.4f}"],
            ['Target Aspect Ratio', f"{cost_function.get('target_aspect_ratio', 1.0):.4f}"],
            ['', ''],
            ['Cost Function', f"{cost_function['cost']:.6f}"],
            ['', ''],
            ['Weights:', ''],
            ['  Area Weight', f"{cost_function['weights'][0]:.2f}"],
            ['  Wirelength Weight', f"{cost_function['weights'][1]:.2f}"],
            ['  Aspect Ratio Weight', f"{cost_function['weights'][2]:.2f}"],
            ['', ''],
            ['Bounding Box:', ''],
            ['  Width', f"{bbox_width:.4f}"],
            ['  Height', f"{bbox_height:.4f}"],
        ]
        
        table = ax2.table(
            cellText=table_data,
            cellLoc='left',
            loc='center',
            colWidths=[0.25, 0.25]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1, 1)
        
        for i in range(2):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        section_rows = [2, 5, 10, 12, 17]
        for row in section_rows:
            table[(row, 0)].set_facecolor('#E8F5E9')
            table[(row, 0)].set_text_props(weight='bold')
        
        plt.tight_layout()
        
        if DISPLAY_MODE == 1:
            plt.show()
        else:
            script_dir = Path(__file__).parent
            placement_dir = script_dir / 'init_placement'
            placement_dir.mkdir(exist_ok=True)
            
            seed = gen_params.get('seed', 0)
            num_blocks = gen_params.get('num_of_blocks', 0)
            
            output_path = placement_dir / f'init_placement_seed{seed}_n{num_blocks}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        result = {
            "generation_params": gen_params,
            "cost_function": cost_function
        }
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Visualization failed"}


def process_n8n_input(json_data):
    """Process input from n8n"""
    result = process_placement_data(json_data)
    return json.loads(json.dumps(result, ensure_ascii=False))


def main_standalone(input_file):
    """Run standalone with input JSON file"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    result = process_placement_data(json_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main_standalone(sys.argv[1])
    elif len(sys.argv) == 1:
        n8n_processor = create_n8n_processor(process_n8n_input)
        n8n_processor()
    else:
        print("Usage:")
        print("  Standalone: python3 04_initial_placement_visualizer.py <input_json_file>")
        print("  n8n mode: cat input.json | python3 04_initial_placement_visualizer.py")
        sys.exit(1)