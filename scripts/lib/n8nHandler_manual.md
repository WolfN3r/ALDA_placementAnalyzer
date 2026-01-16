# N8n JSON Handler - Usage Manual

## 📋 Overview

The `n8n_json_handler.py` provides a universal interface for handling JSON communication between n8n and external Python scripts. It solves ASCII character encoding issues and provides a clean, reusable interface.

## 🚀 Quick Start

### Method 1: Simple Integration (Recommended)

**1. Create your processing script:**

```python
#!/usr/bin/env python3
# my_processor.py

from n8n_json_handler import create_n8n_processor

def my_processing_function(json_data):
    """Your custom processing logic here"""
    
    # Example: Add processing timestamp
    if isinstance(json_data, dict):
        json_data['processed_at'] = '2025-11-21'
        json_data['status'] = 'completed'
    
    # Your actual processing logic goes here
    # ...
    
    return json_data

if __name__ == "__main__":
    # Create n8n-compatible processor
    processor = create_n8n_processor(my_processing_function)
    processor()
```

**2. Use in n8n workflow:**
- Change script path to: `./scripts/my_processor.py`
- Your n8n code stays exactly the same!

---

### Method 2: Custom Handler Usage

```python
#!/usr/bin/env python3
# custom_handler.py

from n8n_json_handler import N8nJsonHandler
import gc

def main():
    handler = N8nJsonHandler()
    
    # Load from n8n
    if not handler.load_from_n8n():
        return
    
    # Get data
    data = handler.get_data()
    
    # Your processing
    processed_data = your_custom_function(data)
    
    # Send back to n8n
    handler.set_output(processed_data)
    handler.output_to_n8n()
    
    # Cleanup
    del data, processed_data
    gc.collect()

def your_custom_function(json_data):
    # Your logic here
    return json_data

if __name__ == "__main__":
    main()
```

---

## 🧪 Testing & Development

### Test with Files (Standalone)

```python
#!/usr/bin/env python3
# test_my_processor.py

from n8n_json_handler import run_processor_from_file

def my_processing_function(json_data):
    # Your processing logic
    json_data['test_mode'] = True
    return json_data

# Test with a JSON file
result = run_processor_from_file('test_input.json', my_processing_function)
if result:
    print("Processing successful!")
    print(result)
else:
    print("Processing failed")
```

### File-to-File Processing

```python
from n8n_json_handler import create_file_processor

def my_processing_function(json_data):
    # Your logic
    return json_data

# Create file processor
file_processor = create_file_processor(my_processing_function)

# Process file and save result
success = file_processor('input.json', 'output.json')
```

---

## 🔧 Advanced Usage Examples

### Memory-Intensive Processing

```python
#!/usr/bin/env python3
# memory_processor.py

from n8n_json_handler import create_n8n_processor
import copy
import gc

def memory_heavy_processing(json_data):
    """Example of memory-intensive operations"""
    
    results = []
    
    # Multiple operations that use memory
    for i in range(5):
        # Safe deepcopy
        copied_data = copy.deepcopy(json_data)
        copied_data['iteration'] = i
        results.append(copied_data)
        
        # Force cleanup every few iterations
        if i % 2 == 0:
            gc.collect()
    
    # Return combined results
    return {
        "original": json_data,
        "processed_copies": results,
        "total_operations": len(results)
    }

if __name__ == "__main__":
    processor = create_n8n_processor(memory_heavy_processing)
    processor()
```

### Multi-Step Processing

```python
#!/usr/bin/env python3
# multi_step_processor.py

from n8n_json_handler import create_n8n_processor

def multi_step_processing(json_data):
    """Example of multi-step data processing"""
    
    # Step 1: Validate input
    if not isinstance(json_data, dict):
        return {"error": "Invalid input format"}
    
    # Step 2: Extract and process items
    if 'items' in json_data:
        for i, item in enumerate(json_data['items']):
            item['processed_index'] = i
            item['validation_status'] = 'passed'
    
    # Step 3: Add metadata
    json_data['processing_steps'] = ['validation', 'item_processing', 'metadata_addition']
    json_data['total_items'] = len(json_data.get('items', []))
    
    # Step 4: Create summary
    json_data['summary'] = {
        'processed': True,
        'step_count': 4,
        'status': 'success'
    }
    
    return json_data

if __name__ == "__main__":
    processor = create_n8n_processor(multi_step_processing)
    processor()
```

---

## ⚡ Integration Patterns

### Pattern 1: Replace Existing Script
1. Keep your existing n8n node code unchanged
2. Replace `script_path` with your new script
3. Your script uses `create_n8n_processor()` wrapper

### Pattern 2: Import as Module
```python
# In your existing script
from n8n_json_handler import N8nJsonHandler

def main():
    handler = N8nJsonHandler()
    # ... rest of your logic
```

### Pattern 3: Hybrid Approach
```python
# For scripts that need both n8n and file support
from n8n_json_handler import create_n8n_processor, create_file_processor

def my_processor(json_data):
    # Your logic here
    return json_data

# Create both versions
n8n_version = create_n8n_processor(my_processor)
file_version = create_file_processor(my_processor)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # File mode: python script.py input.json [output.json]
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        file_version(input_file, output_file)
    else:
        # n8n mode
        n8n_version()
```

---

## 🛡️ Error Handling Best Practices

### Always Return Valid JSON
```python
def safe_processing_function(json_data):
    try:
        # Your processing logic
        result = process_data(json_data)
        return {"success": True, "data": result}
    except Exception as e:
        # Return error in valid JSON format
        return {"success": False, "error": str(e), "data": None}
```

### Handle Large Data Sets
```python
def memory_safe_processing(json_data):
    # Process in chunks if data is large
    if isinstance(json_data, dict) and 'items' in json_data:
        items = json_data['items']
        if len(items) > 1000:
            # Process in smaller chunks
            chunk_size = 100
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                # Process chunk
                # ... your logic
                gc.collect()  # Force cleanup
    
    return json_data
```

---

## 🔍 Troubleshooting

### Common Issues & Solutions

1. **"Non-ASCII character" error**
   - ✅ **Fixed automatically** by the handler's safe encoding

2. **Memory issues**
   - Use `gc.collect()` after processing large chunks
   - Process data in smaller batches
   - Delete large variables with `del variable_name`

3. **JSON serialization errors**
   - Ensure all data is JSON-serializable (no functions, custom objects)
   - Use `str()` to convert problematic values

4. **n8n workflow hangs**
   - Always ensure your script outputs valid JSON
   - Check that `if __name__ == "__main__":` block runs correctly
   - Test with files first before using in n8n

### Testing Checklist
- [ ] Script works standalone with test JSON file
- [ ] Script outputs valid JSON (test with `json.loads()`)
- [ ] No print statements outside of the handler output
- [ ] Proper error handling implemented
- [ ] Memory cleanup included for large operations

---

## 📁 File Structure Example

```
project/
├── n8n_json_handler.py          # Universal handler (this file)
├── scripts/
│   ├── my_processor.py          # Your processing script
│   ├── memory_test.py           # Memory testing script  
│   └── data_transformer.py     # Data transformation script
└── test_data/
    ├── input.json               # Test input file
    └── expected_output.json     # Expected results
```

This manual should get you started with clean, reliable n8n-Python integration! 🚀