#!/usr/bin/env python3
"""
B*-tree Simulated Annealing Optimizer - Fixed Node Preservation
Paper: "Module Placement with Boundary Constraints Using B*-trees"
"""

import json
import random
import math
from n8n_json_handler import create_n8n_processor

# SA SETTINGS
INITIAL_TEMP = 1000.0
FINAL_TEMP = 0.01
COOLING_RATE = 0.999
MAX_ITERATIONS = 50000

# COST FUNCTION WEIGHTS
AREA_WEIGHT = 10.0
DEAD_SPACE_WEIGHT = 1000.0
ASPECT_RATIO_WEIGHT = 1000.0
TARGET_ASPECT_RATIO = 1.0
MAX_ASPECT_RATIO = 1.5

ASPECT_PENALTY = 100000.0


class SimpleOptimizer:
    """Optimizer implementing exact B*-tree packing from paper"""

    def __init__(self, json_data):
        self.data = json_data
        self.variants = self._get_variants()
        self.actual_iterations = 0

    def _get_variants(self):
        """Extract block variants safely"""
        variants = {}
        try:
            for block in self.data.get("blocks", []):
                name = block["name"]
                variants[name] = []
                for variant in block["variants"]:
                    variants[name].append({
                        "width": float(variant["width"]),
                        "height": float(variant["height"])
                    })
        except:
            pass
        return variants

    def _get_all_nodes_from_dict(self, node_dict, nodes_list=None):
        """Get all nodes from tree via DFS"""
        if nodes_list is None:
            nodes_list = []

        if not node_dict or not isinstance(node_dict, dict):
            return nodes_list

        if "name" in node_dict:
            nodes_list.append(node_dict)

        x_child = node_dict.get("x_child", {})
        y_child = node_dict.get("y_child", {})

        if x_child:
            self._get_all_nodes_from_dict(x_child, nodes_list)
        if y_child:
            self._get_all_nodes_from_dict(y_child, nodes_list)

        return nodes_list

    def _safe_copy_tree(self, tree_dict):
        """Safe tree copying"""
        if not tree_dict or not isinstance(tree_dict, dict):
            return {}

        try:
            return {
                "name": tree_dict.get("name", ""),
                "x_min": float(tree_dict.get("x_min", 0)),
                "y_min": float(tree_dict.get("y_min", 0)),
                "x_max": float(tree_dict.get("x_max", 0)),
                "y_max": float(tree_dict.get("y_max", 0)),
                "x_child": self._safe_copy_tree(tree_dict.get("x_child", {})),
                "y_child": self._safe_copy_tree(tree_dict.get("y_child", {}))
            }
        except:
            return tree_dict

    def _op1_change_variant(self, tree_dict):
        """Op1: Rotate/change variant (Paper Section 5.1)"""
        try:
            nodes = self._get_all_nodes_from_dict(tree_dict)
            if not nodes:
                return tree_dict

            node = random.choice(nodes)
            name = node.get("name", "")

            if name in self.variants and len(self.variants[name]) > 1:
                variant = random.choice(self.variants[name])
                width = variant["width"]
                height = variant["height"]

                # Only change dimensions, not tree structure
                node["x_max"] = node["x_min"] + width
                node["y_max"] = node["y_min"] + height

        except:
            pass

        return tree_dict

    def _op2_swap_nodes(self, tree_dict):
        """
        Op2: Swap node MODULE DATA ONLY (Paper Section 5.1)
        CRITICAL FIX: Only swap name and dimensions, NOT children!
        """
        try:
            nodes = self._get_all_nodes_from_dict(tree_dict)
            if len(nodes) < 2:
                return tree_dict

            node1, node2 = random.sample(nodes, 2)

            # Calculate current dimensions for both nodes
            width1 = node1.get("x_max", 0) - node1.get("x_min", 0)
            height1 = node1.get("y_max", 0) - node1.get("y_min", 0)
            width2 = node2.get("x_max", 0) - node2.get("x_min", 0)
            height2 = node2.get("y_max", 0) - node2.get("y_min", 0)

            # Swap ONLY module names and dimensions (keep children intact)
            temp_name = node1.get("name", "")
            node1["name"] = node2.get("name", "")
            node2["name"] = temp_name

            # Update dimensions based on swapped modules
            node1["x_max"] = node1["x_min"] + width2
            node1["y_max"] = node1["y_min"] + height2
            node2["x_max"] = node2["x_min"] + width1
            node2["y_max"] = node2["y_min"] + height1

            # DO NOT touch x_child or y_child - tree structure stays intact!

        except:
            pass

        return tree_dict

    def _find_node_and_parent(self, tree_dict, target_node, parent=None, child_type=None):
        """Find node and its parent in tree"""
        if not tree_dict or not isinstance(tree_dict, dict):
            return None

        if tree_dict is target_node:
            return (parent, child_type)

        result = self._find_node_and_parent(tree_dict.get("x_child"), target_node, tree_dict, "x_child")
        if result:
            return result

        result = self._find_node_and_parent(tree_dict.get("y_child"), target_node, tree_dict, "y_child")
        if result:
            return result

        return None

    def _op3_move_node(self, tree_dict):
        """
        Op3: Move node (Paper Section 5.1, Figure 9)
        Delete node -> promote children -> insert node elsewhere
        """
        try:
            nodes = self._get_all_nodes_from_dict(tree_dict)
            if len(nodes) < 3:
                return tree_dict

            # Cannot move root
            moveable = [n for n in nodes if n is not tree_dict]
            if not moveable:
                return tree_dict

            node_to_move = random.choice(moveable)

            # STEP 1: DELETE - Find parent and extract node
            parent_info = self._find_node_and_parent(tree_dict, node_to_move)
            if not parent_info or not parent_info[0]:
                return tree_dict

            parent, child_type = parent_info
            x_child = node_to_move.get("x_child", {})
            y_child = node_to_move.get("y_child", {})

            # Promote children according to paper's algorithm
            if x_child and y_child:
                # Node has two children: randomly pick one to promote
                promoted = random.choice([x_child, y_child])
                other = y_child if promoted is x_child else x_child
                parent[child_type] = promoted

                # Attach other child to leaf of promoted subtree
                current = promoted
                while current:
                    if not current.get("x_child"):
                        current["x_child"] = other
                        break
                    elif not current.get("y_child"):
                        current["y_child"] = other
                        break
                    current = current.get("x_child")
            elif x_child:
                # Only x_child exists
                parent[child_type] = x_child
            elif y_child:
                # Only y_child exists
                parent[child_type] = y_child
            else:
                # Leaf node
                parent[child_type] = {}

            # STEP 2: INSERT - Clear node's children and insert fresh
            node_to_move["x_child"] = {}
            node_to_move["y_child"] = {}

            # Get updated node list after deletion
            all_nodes = self._get_all_nodes_from_dict(tree_dict)
            if not all_nodes:
                return tree_dict

            # Choose random parent for insertion
            new_parent = random.choice(all_nodes)

            # Insert as random child (x_child or y_child)
            if random.random() < 0.5:
                # Insert as x_child
                original_x_child = new_parent.get("x_child", {})
                new_parent["x_child"] = node_to_move
                if original_x_child:
                    node_to_move["x_child"] = original_x_child
            else:
                # Insert as y_child
                original_y_child = new_parent.get("y_child", {})
                new_parent["y_child"] = node_to_move
                if original_y_child:
                    node_to_move["y_child"] = original_y_child

        except:
            pass

        return tree_dict

    def _contour_placement(self, tree_dict):
        """Recompute placement using contour (Paper Section 3)"""
        try:
            contour = []
            self._dfs_place(tree_dict, None, None, contour)
        except:
            pass
        return tree_dict

    def _dfs_place(self, node, parent, is_left_child, contour):
        """DFS traversal for placement"""
        if not node or not isinstance(node, dict) or "name" not in node:
            return

        try:
            width = node.get("x_max", 0) - node.get("x_min", 0)
            height = node.get("y_max", 0) - node.get("y_min", 0)

            # Determine X coordinate
            if parent is None:
                # Root at origin
                x_coord = 0.0
            elif is_left_child:
                # Left child: right of parent
                parent_width = parent.get("x_max", 0) - parent.get("x_min", 0)
                x_coord = parent.get("x_min", 0) + parent_width
            else:
                # Right child: same X as parent
                x_coord = parent.get("x_min", 0)

            # Find Y from contour
            y_coord = self._find_y_from_contour(contour, x_coord, x_coord + width)

            # Update node position
            node["x_min"] = x_coord
            node["y_min"] = y_coord
            node["x_max"] = x_coord + width
            node["y_max"] = y_coord + height

            # Update contour
            self._update_contour(contour, x_coord, x_coord + width, y_coord + height)

            # Recurse on children
            if node.get("x_child"):
                self._dfs_place(node["x_child"], node, True, contour)

            if node.get("y_child"):
                self._dfs_place(node["y_child"], node, False, contour)

        except:
            pass

    def _find_y_from_contour(self, contour, x_start, x_end):
        """Find Y coordinate from contour"""
        max_y = 0.0
        try:
            for c_start, c_end, c_top in contour:
                if c_start < x_end and c_end > x_start:
                    max_y = max(max_y, c_top)
        except:
            pass
        return max_y

    def _update_contour(self, contour, x_start, x_end, y_top):
        """Update contour structure"""
        try:
            new_contour = []

            for c_start, c_end, c_top in contour:
                if c_end <= x_start or c_start >= x_end:
                    # No overlap
                    new_contour.append((c_start, c_end, c_top))
                elif c_start < x_start < c_end:
                    # Partial overlap on left
                    new_contour.append((c_start, x_start, c_top))
                    if c_end > x_end:
                        new_contour.append((x_end, c_end, c_top))
                elif c_start < x_end < c_end:
                    # Partial overlap on right
                    new_contour.append((x_end, c_end, c_top))

            # Add new segment
            new_contour.append((x_start, x_end, y_top))
            new_contour.sort()

            contour.clear()
            contour.extend(new_contour)

        except:
            pass

    def _calculate_fitness(self, tree_dict):
        """Calculate fitness score"""
        try:
            self._contour_placement(tree_dict)
            nodes = self._get_all_nodes_from_dict(tree_dict)

            if not nodes:
                return 999999

            max_x = max(node.get("x_max", 0) for node in nodes)
            max_y = max(node.get("y_max", 0) for node in nodes)

            if max_x <= 0 or max_y <= 0:
                return 999999

            total_area = max_x * max_y
            used_area = sum((node.get("x_max", 0) - node.get("x_min", 0)) *
                            (node.get("y_max", 0) - node.get("y_min", 0)) for node in nodes)

            dead_space = total_area - used_area
            dead_space_ratio = dead_space / total_area if total_area > 0 else 0

            aspect_ratio = max(max_x, max_y) / min(max_x, max_y)

            if aspect_ratio > MAX_ASPECT_RATIO:
                aspect_penalty = ASPECT_PENALTY * (aspect_ratio - MAX_ASPECT_RATIO)
            else:
                aspect_penalty = abs(aspect_ratio - TARGET_ASPECT_RATIO) * ASPECT_RATIO_WEIGHT

            dead_space_penalty = dead_space_ratio * DEAD_SPACE_WEIGHT
            fitness = total_area * AREA_WEIGHT + aspect_penalty + dead_space_penalty

            return fitness

        except:
            return 999999

    def optimize(self):
        """Simulated annealing optimization"""
        try:
            current_tree = self.data.get("bstar_tree", {}).get("root", {})
            if not current_tree:
                return None, 999999, 0

            current_fitness = self._calculate_fitness(current_tree)
            best_tree = self._safe_copy_tree(current_tree)
            best_fitness = current_fitness

            temperature = INITIAL_TEMP

            for iteration in range(MAX_ITERATIONS):
                self.actual_iterations = iteration + 1

                if temperature < FINAL_TEMP:
                    break

                new_tree = self._safe_copy_tree(current_tree)

                # Operation probabilities (vary with temperature)
                temp_ratio = temperature / INITIAL_TEMP
                op1_prob = 0.33 + (1.0 - temp_ratio) * 0.47
                op2_prob = 0.33 * temp_ratio + 0.15 * (1.0 - temp_ratio)

                rand_val = random.random()
                if rand_val < op1_prob:
                    new_tree = self._op1_change_variant(new_tree)
                elif rand_val < op1_prob + op2_prob:
                    new_tree = self._op2_swap_nodes(new_tree)
                else:
                    new_tree = self._op3_move_node(new_tree)

                new_fitness = self._calculate_fitness(new_tree)

                # Accept better solutions
                if new_fitness < current_fitness:
                    current_tree = new_tree
                    current_fitness = new_fitness

                    if new_fitness < best_fitness:
                        best_tree = self._safe_copy_tree(new_tree)
                        best_fitness = new_fitness
                else:
                    # Accept worse solutions probabilistically
                    delta = new_fitness - current_fitness
                    if temperature > 0:
                        prob = math.exp(-delta / temperature)
                        if random.random() < prob:
                            current_tree = new_tree
                            current_fitness = new_fitness

                temperature *= COOLING_RATE

            return best_tree, best_fitness, self.actual_iterations

        except Exception as e:
            return None, 999999, self.actual_iterations


def optimize_bstar_tree_safe(json_data):
    """Safe optimizer wrapper"""
    if not json_data or not isinstance(json_data, dict):
        return {"error": "Invalid input data"}

    if "bstar_tree" not in json_data:
        return {"error": "No bstar_tree in input"}

    if "blocks" not in json_data:
        return {"error": "No blocks in input"}

    try:
        optimizer = SimpleOptimizer(json_data)
        best_tree, best_fitness, iterations = optimizer.optimize()

        if best_tree is None:
            return {"error": "Optimization failed"}

        optimizer._contour_placement(best_tree)
        nodes = optimizer._get_all_nodes_from_dict(best_tree)

        if not nodes:
            return {"error": "No nodes in result"}

        max_x = max(node.get("x_max", 0) for node in nodes)
        max_y = max(node.get("y_max", 0) for node in nodes)
        total_area = max_x * max_y
        used_area = sum((node.get("x_max", 0) - node.get("x_min", 0)) *
                        (node.get("y_max", 0) - node.get("y_min", 0)) for node in nodes)
        dead_space = total_area - used_area
        dead_space_ratio = (dead_space / total_area * 100) if total_area > 0 else 0
        aspect_ratio = max(max_x, max_y) / min(max_x, max_y) if min(max_x, max_y) > 0 else 1.0

        result = dict(json_data)
        result["bstar_tree"] = {"root": best_tree}
        result["optimization_results"] = {
            "fitness_function": round(best_fitness, 2),
            "total_area": round(total_area, 2),
            "used_area": round(used_area, 2),
            "dead_space": round(dead_space, 2),
            "dead_space_percentage": round(dead_space_ratio, 2),
            "aspect_ratio": round(aspect_ratio, 2),
            "placement_width": round(max_x, 2),
            "placement_height": round(max_y, 2),
            "actual_iterations": iterations,
            "optimization_method": "fixed_node_preservation"
        }

        return result

    except Exception as e:
        return {"error": f"Optimization error: {str(e)}"}


if __name__ == "__main__":
    processor = create_n8n_processor(optimize_bstar_tree_safe)
    processor()