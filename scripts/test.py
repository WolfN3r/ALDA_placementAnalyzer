#!/usr/bin/env python3
"""
Test JSON Saver - Saves n8n JSON to test/test.json and returns it
"""

from pathlib import Path
import json
import sys

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from n8n_json_handler import create_n8n_processor


def save_and_return(json_data):
    """Save JSON to test directory and return it"""
    
    # Create test directory relative to script location
    script_dir = Path(__file__).parent
    test_dir = script_dir / "test"
    test_dir.mkdir(exist_ok=True)
    
    # Save to test.json
    output_file = test_dir / "test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Return same data to n8n
    return json_data


if __name__ == "__main__":
    processor = create_n8n_processor(save_and_return)
    processor()