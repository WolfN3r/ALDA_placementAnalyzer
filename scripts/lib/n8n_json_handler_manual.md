# N8n JSON Handler - Usage Manual

## 📋 Overview

The `n8n_json_handler.py` provides a universal interface for handling JSON communication between n8n and external Python scripts. It solves ASCII character encoding issues and provides a clean, reusable interface.

## ✨ Automatic Features

### Auto-Unwrapping of Batch Structure
When n8n Python nodes receive multiple items, they wrap them in `{"batch": [...]}` structure. This handler **automatically unwraps** this structure so your scripts receive clean data directly.

**Example:**
- **Input from n8n:** `{"batch": [item1, item2, item3]}`  
- **What your script receives:** `[item1, item2, item3]`

This happens transparently - you don't need to handle it in your code!

### UTF-8 Character Safety
All output data is automatically sanitized to ensure UTF-8 compatibility. Non-UTF-8 characters are replaced, preventing encoding errors that crash n8n workflows.

This is especially important when:
- Processing file paths (e.g., `/home/node/scripts/file.png`)
- Handling international characters
- Working with data from various sources

---

## 🚀 Quick Start

### Method 1: Simple Integration (Recommended)

**1. Create your processing script:**

```python
#!/usr/bin/env python3
# my_processor.py

from n8n_json_handler import create_n8n_processor

def my_processing_function(json_data):
    """Your custom processing logic here"""
    
    # json_data is already unwrapped if it came from {"batch": [...]}
    # You can work with it directly!
    
    if isinstance(json_data, list):
        # Process list of items
        for item in json_data:
            # Your logic here
            pass
    elif isinstance(json_data, dict):
        # Process single item
        pass
    
    return json_data

if __name__ == "__main__":
    # Create n8n-compatible processor
    processor = create_n8n_processor(my_processing_function)
    processor()
```

**2. Use in n8n workflow:**
- Change script path to: `./scripts/my_processor.py`
- Your n8n code stays exactly the same!
- The handler automatically unwraps batch structures

---

### Method 2: Custom Handler Usage

```python
#!/usr/bin/env python3
# custom_handler.py

from n8n_json_handler import N8nJsonHandler
import gc

def main():
    handler = N8nJsonHandler()
    
    # Load from n8n (auto-unwraps batch structure)
    if not handler.load_from_n8n():
        return
    
    # Get data (already unwrapped!)
    data = handler.get_data()
    
    # Your processing
    processed_data = your_custom_function(data)
    
    # Send back to n8n (with UTF-8 safety)
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

The handler also unwraps batch structures when loading from files!

```python
#!/usr/bin/env python3
# test_my_processor.py

from n8n_json_handler import run_processor_from_file

def my_processing_function(json_data):
    # json_data is unwrapped automatically
    print(f"Received {len(json_data)} items" if isinstance(json_data, list) else "Received 1 item")
    return json_data

# Test with a JSON file (works with both formats)
result = run_processor_from_file('test_input.json', my_processing_function)
if result:
    print("Processing successful!")
else:
    print("Processing failed")
```

**Test files can be in either format:**
- `[item1, item2, item3]` - Direct array
- `{"batch": [item1, item2, item3]}` - Batch wrapped (auto-unwrapped)

### File-to-File Processing

```python
from n8n_json_handler import create_file_processor

def my_processing_function(json_data):
    # Your logic (receives unwrapped data)
    return json_data

# Create file processor
file_processor = create_file_processor(my_processing_function)

# Process file and save result
success = file_processor('input.json', 'output.json')
```

---

## 🔧 Advanced Usage Examples

### Processing Multiple Items from n8n

```python
#!/usr/bin/env python3
# multi_item_processor.py

from n8n_json_handler import create_n8n_processor

def process_multiple_items(json_data):
    """
    Works seamlessly with n8n's batch structure
    The {"batch": [...]} is automatically unwrapped!
    """
    
    results = []
    
    # If data is list (from unwrapped batch)
    if isinstance(json_data, list):
        for item in json_data:
            # Process each item
            item['processed'] = True
            item['timestamp'] = '2026-01-17'
            results.append(item)
    else:
        # Single item
        json_data['processed'] = True
        results = json_data
    
    return results

if __name__ == "__main__":
    processor = create_n8n_processor(process_multiple_items)
    processor()
```

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
    
    # Data is already unwrapped from batch structure
    items = json_data if isinstance(json_data, list) else [json_data]
    
    for i, item in enumerate(items):
        # Safe deepcopy
        copied_data = copy.deepcopy(item)
        copied_data['iteration'] = i
        results.append(copied_data)
        
        # Force cleanup every few iterations
        if i % 2 == 0:
            gc.collect()
    
    return results

if __name__ == "__main__":
    processor = create_n8n_processor(memory_heavy_processing)
    processor()
```

---

## ⚡ Integration Patterns

### Pattern 1: Replace Existing Script
1. Keep your existing n8n node code unchanged
2. Replace `script_path` with your new script
3. Your script uses `create_n8n_processor()` wrapper
4. **Batch structures are automatically unwrapped!**

### Pattern 2: Import as Module
```python
# In your existing script
from n8n_json_handler import N8nJsonHandler

def main():
    handler = N8nJsonHandler()
    # Batch unwrapping happens automatically in load_from_n8n()
```

### Pattern 3: Hybrid Approach (n8n + File Testing)
```python
# For scripts that need both n8n and file support
from n8n_json_handler import create_n8n_processor, create_file_processor

def my_processor(json_data):
    # json_data is already unwrapped in both modes!
    return json_data

# Create both versions
n8n_version = create_n8n_processor(my_processor)
file_version = create_file_processor(my_processor)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # File mode
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
    # Data is already unwrapped, can be list or dict
    items = json_data if isinstance(json_data, list) else [json_data]
    
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
   - ✅ **Fixed automatically** by UTF-8 sanitization

2. **"Batch structure not unwrapping"**
   - ✅ **Fixed automatically** - handler unwraps `{"batch": [...]}` 
   - Works in both `load_from_n8n()` and `load_from_file()`

3. **Memory issues**
   - Use `gc.collect()` after processing large chunks
   - Process data in smaller batches
   - Delete large variables with `del variable_name`

4. **JSON serialization errors**
   - Ensure all data is JSON-serializable (no functions, custom objects)
   - Use `str()` to convert problematic values
   - UTF-8 sanitization handles most character issues automatically

5. **n8n workflow hangs**
   - Always ensure your script outputs valid JSON
   - Check that `if __name__ == "__main__":` block runs correctly
   - Test with files first before using in n8n

### Testing Checklist
- [ ] Script works standalone with test JSON file
- [ ] Script works with both array and batch-wrapped formats
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
│   └── data_transformer.py      # Data transformation script
└── test_data/
    ├── input.json               # Test input (array format)
    ├── input_batch.json         # Test input (batch format)
    └── expected_output.json     # Expected results
```

---

## 🔑 Key Features Summary

| Feature | Benefit |
|---------|---------|
| **Auto Batch Unwrapping** | Handles `{"batch": [...]}` automatically - your code stays clean |
| **UTF-8 Sanitization** | Prevents encoding crashes - automatically fixes character issues |
| **Safe Encoding** | Handles ASCII character issues automatically |
| **Dual Mode** | Works seamlessly in both n8n and file testing |
| **Memory Management** | Built-in garbage collection support |
| **Error Handling** | Consistent JSON error responses |

---

This manual should get you started with clean, reliable n8n-Python integration! 🚀

**New in this version:**
- ✨ Automatic `{"batch": [...]}` unwrapping
- ✨ UTF-8 character safety and sanitization
- ✨ Works transparently in all modes (n8n, file input, file-to-file)