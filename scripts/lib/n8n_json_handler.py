#!/usr/bin/env python3
"""
Universal n8n JSON Handler
Handles JSON communication between n8n and external Python scripts with safe encoding
"""

import json
import sys
import gc


class N8nJsonHandler:
    """Universal handler for n8n JSON communication with safe encoding"""

    def __init__(self):
        self.input_data = None
        self.output_data = None

    def load_from_n8n(self):
        """
        Safely load JSON from n8n stdin with proper encoding handling
        Returns: True if successful, False otherwise
        """
        try:
            # Safe encoding handling - prevents ASCII character issues
            input_bytes = sys.stdin.buffer.read()
            input_text = input_bytes.decode('utf-8', errors='replace')
            self.input_data = json.loads(input_text)
            return True
        except Exception as e:
            self._output_error(f"Failed to load JSON from n8n: {str(e)}")
            return False

    def load_from_file(self, filename):
        """
        Load JSON from file (for standalone testing)
        Args:
            filename (str): Path to JSON file
        Returns: True if successful, False otherwise
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.input_data = json.load(f)
            return True
        except Exception as e:
            self._output_error(f"Failed to load JSON from file {filename}: {str(e)}")
            return False

    def get_data(self):
        """
        Get the loaded data for processing
        Returns: Loaded JSON data or None
        """
        return self.input_data

    def set_output(self, data):
        """
        Set the output data to be sent back to n8n
        Args:
            data: Any JSON-serializable data structure
        """
        self.output_data = data

    def output_to_n8n(self):
        """
        Safely output JSON to n8n stdout with proper encoding
        """
        if self.output_data is not None:
            try:
                # Safe JSON output - prevents ASCII character issues
                output_text = json.dumps(self.output_data, ensure_ascii=False, separators=(',', ':'))
                print(output_text)
            except Exception as e:
                self._output_error(f"Failed to serialize output: {str(e)}")
        else:
            self._output_error("No output data set")

    def _output_error(self, error_message):
        """
        Output error in n8n-compatible format
        Args:
            error_message (str): Error description
        """
        error_response = {
            "error": error_message,
            "success": False,
            "data": None
        }
        try:
            print(json.dumps(error_response, ensure_ascii=False))
        except:
            print('{"error": "Critical JSON serialization error", "success": false}')


def create_n8n_processor(user_processor_function):
    """
    Universal function that wraps user processing logic for n8n

    Args:
        user_processor_function: Function that takes JSON data and returns processed JSON
                                Signature: user_function(json_data) -> processed_json_data

    Returns: Function ready for n8n execution
    """

    def n8n_wrapper():
        handler = N8nJsonHandler()

        # Load input from n8n
        if not handler.load_from_n8n():
            return  # Error already output by handler

        # Get data for processing
        input_data = handler.get_data()

        try:
            # Call user's processing function
            processed_data = user_processor_function(input_data)

            # Set output and send to n8n
            handler.set_output(processed_data)
            handler.output_to_n8n()

            # Cleanup
            del input_data, processed_data
            gc.collect()

        except Exception as e:
            handler._output_error(f"Processing error: {str(e)}")

    return n8n_wrapper


def create_file_processor(user_processor_function):
    """
    Universal function that wraps user processing logic for file-based testing

    Args:
        user_processor_function: Function that takes JSON data and returns processed JSON

    Returns: Function that can process files
    """

    def file_wrapper(input_filename, output_filename=None):
        handler = N8nJsonHandler()

        # Load input from file
        if not handler.load_from_file(input_filename):
            return False

        # Get data for processing
        input_data = handler.get_data()

        try:
            # Call user's processing function
            processed_data = user_processor_function(input_data)

            # Output to file or stdout
            if output_filename:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)
                print(f"Output saved to: {output_filename}")
            else:
                handler.set_output(processed_data)
                handler.output_to_n8n()

            # Cleanup
            del input_data, processed_data
            gc.collect()

            return True

        except Exception as e:
            print(f"Processing error: {str(e)}", file=sys.stderr)
            return False

    return file_wrapper


def run_processor_from_file(filename, user_processor_function):
    """
    Convenience function to run processor with JSON file input

    Args:
        filename (str): Path to input JSON file
        user_processor_function: User's processing function

    Returns: Processed data or None if error
    """
    handler = N8nJsonHandler()

    if not handler.load_from_file(filename):
        return None

    try:
        input_data = handler.get_data()
        result = user_processor_function(input_data)

        # Cleanup
        del input_data
        gc.collect()

        return result

    except Exception as e:
        print(f"Processing error: {str(e)}", file=sys.stderr)
        return None


# Example usage and testing
def example_processor(json_data):
    """
    Example processing function - replace with your logic

    Args:
        json_data: Input JSON data from n8n or file

    Returns: Processed JSON data
    """
    if isinstance(json_data, dict):
        # Add processing metadata
        json_data['processed'] = True
        json_data['example_processing'] = 'completed'

        # Example: count items if present
        if 'items' in json_data and isinstance(json_data['items'], list):
            json_data['item_count'] = len(json_data['items'])
            json_data['processing_summary'] = f"Processed {len(json_data['items'])} items"

    return json_data


if __name__ == "__main__":
    # For n8n integration - create processor and run
    n8n_processor = create_n8n_processor(example_processor)
    n8n_processor()