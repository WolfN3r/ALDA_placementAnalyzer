#!/usr/bin/env python3
"""
Simple n8n processor that loads simplified devices JSON file
"""

import json
import os
from lib.n8n_json_handler import create_n8n_processor


def load_simplified_devices(json_data):
    """
    Load simplified devices JSON from static file and return it directly

    Args:
        json_data: Input JSON data from n8n (ignored for this use case)

    Returns:
        Raw simplified devices JSON structure
    """

    # Static file path to the simplified devices JSON
    # Use absolute path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "lib/gpdk090_tech_simple.json")

    try:
        # Load and return the simplified devices JSON directly
        with open(file_path, 'r', encoding='utf-8') as f:
            devices_data = json.load(f)

        return devices_data

    except Exception as e:
        # Return minimal error structure if something goes wrong
        return {
            "error": f"Failed to load file: {str(e)}",
            "file_path": file_path,
            "script_dir": script_dir
        }


if __name__ == "__main__":
    # Create n8n-compatible processor
    processor = create_n8n_processor(load_simplified_devices)
    processor()