# Layout Analysis Library

A Python library for analyzing and visualizing analog layout optimization algorithms in Electronic Design Automation (EDA).

## Overview

This library provides tools for tracking, analyzing, and visualizing the performance of layout optimization algorithms such as Simulated Annealing (SA), Genetic Algorithms (GA), and other metaheuristics used in analog circuit layout design.

## Features

- **Cost Calculation**: Weighted multi-objective cost functions for area, wirelength, and aspect ratio
- **Data Logging**: Track optimization progress over iterations
- **Convergence Analysis**: Visualize how cost decreases over time
- **Trajectory Plotting**: Show the optimization path through the design space
- **Statistical Analysis**: Analyze multiple runs with histogram and Gaussian fitting
- **Method Comparison**: Compare different optimization algorithms side-by-side

## Installation

### Requirements

```bash
pip install numpy matplotlib scipy
```

### Usage

Simply import the library:

```python
import layout_analysis as la
```

Or import specific functions:

```python
from layout_analysis import wmi_calculate_cost, wmi_log_step
```

## API Reference

### Cost Calculation

#### `wmi_calculate_cost(area, wirelength, aspect_ratio, init_area, init_wirelength, target_ar, weights)`

Calculates a weighted multi-objective cost function.

**Formula:**
```
Cost = w₀ × (Area / Area_init) + w₁ × (WL / WL_init) + w₂ × (AR - AR_target)²
```

**Parameters:**
- `area` (float): Current layout area
- `wirelength` (float): Current total wirelength
- `aspect_ratio` (float): Current aspect ratio
- `init_area` (float): Initial or normalization area (use 1.0 for absolute cost)
- `init_wirelength` (float): Initial or normalization wirelength (use 1.0 for absolute cost)
- `target_ar` (float): Target aspect ratio
- `weights` (tuple): Three-element tuple (w₀, w₁, w₂) for weighting each term

**Returns:**
- `float`: Calculated cost value

**Example:**
```python
cost = wmi_calculate_cost(
    area=120.5,
    wirelength=450.2,
    aspect_ratio=1.2,
    init_area=100.0,
    init_wirelength=500.0,
    target_ar=1.0,
    weights=(0.4, 0.4, 0.2)
)
```

### Data Logging

#### `wmi_log_step(log_data, iteration, time_val, cost, area, wirelength, aspect_ratio)`

Appends optimization step data to the log.

**Parameters:**
- `log_data` (list): Existing log data (list of dictionaries)
- `iteration` (int): Current iteration number
- `time_val` (float): Time elapsed (in seconds or arbitrary units)
- `cost` (float): Current cost value
- `area` (float): Current area
- `wirelength` (float): Current wirelength
- `aspect_ratio` (float): Current aspect ratio

**Returns:**
- `list`: Updated log_data with new entry appended

**Example:**
```python
log_data = []
log_data = wmi_log_step(log_data, 0, 0.0, 1.5, 100.0, 500.0, 1.0)
log_data = wmi_log_step(log_data, 1, 0.1, 1.3, 95.0, 480.0, 1.05)
```

### Data Export

#### `wmi_save_csv(log_data, filename)`

Saves log data to a CSV file with headers.

**Parameters:**
- `log_data` (list): Log data to save
- `filename` (str): Output CSV filename

**Example:**
```python
wmi_save_csv(log_data, 'optimization_log.csv')
```

### Visualization

#### `wmi_plot_convergence(log_data, output_filename)`

Creates a Time vs Cost convergence plot.

**Parameters:**
- `log_data` (list): Log data containing Time and Cost
- `output_filename` (str): Output image filename (e.g., 'convergence.png')

**Example:**
```python
wmi_plot_convergence(log_data, 'sa_convergence.png')
```

#### `wmi_plot_trajectory(log_data, output_filename)`

Creates an Area vs Wirelength trajectory plot with color-coded iterations.

**Color Scheme:** Red (start) → Blue (end), visualizing optimization "cooling"

**Parameters:**
- `log_data` (list): Log data containing Area and Wirelength
- `output_filename` (str): Output image filename

**Example:**
```python
wmi_plot_trajectory(log_data, 'sa_trajectory.png')
```

### Statistical Analysis

#### `wmi_analyze_statistics(final_results_list, output_filename)`

Analyzes multiple optimization runs and fits a Gaussian distribution.

**Parameters:**
- `final_results_list` (list): List of final cost values from multiple runs
- `output_filename` (str): Output image filename for histogram with Gaussian fit

**Returns:**
- `tuple`: (mean, standard_deviation)

**Example:**
```python
final_costs = [1.25, 1.18, 1.30, 1.22, 1.27, 1.20, 1.24, 1.26, 1.21, 1.23]
mean, std = wmi_analyze_statistics(final_costs, 'statistics.png')
print(f'Mean: {mean:.4f}, Std Dev: {std:.4f}')
```

### Method Comparison

#### `wmi_compare_methods(method_logs, method_names, output_filename)`

Compares multiple optimization methods on a single plot.

**Parameters:**
- `method_logs` (list): List of log_data structures from different methods
- `method_names` (list): List of method names for the legend
- `output_filename` (str): Output image filename

**Example:**
```python
wmi_compare_methods(
    [sa_log, ga_log, pso_log],
    ['Simulated Annealing', 'Genetic Algorithm', 'Particle Swarm'],
    'method_comparison.png'
)
```

## Complete Example

```python
import layout_analysis as la
import time

log_data = []
init_area = 100.0
init_wl = 500.0
target_ar = 1.0
weights = (0.4, 0.4, 0.2)

for i in range(100):
    current_time = i * 0.01
    area = 100.0 - i * 0.3
    wl = 500.0 - i * 2.0
    ar = 1.0 + (i % 10) * 0.01
    
    cost = la.wmi_calculate_cost(
        area, wl, ar, init_area, init_wl, target_ar, weights
    )
    
    log_data = la.wmi_log_step(
        log_data, i, current_time, cost, area, wl, ar
    )

la.wmi_save_csv(log_data, 'optimization.csv')
la.wmi_plot_convergence(log_data, 'convergence.png')
la.wmi_plot_trajectory(log_data, 'trajectory.png')

final_costs = [log_data[-1]['Cost'] for _ in range(20)]
mean, std = la.wmi_analyze_statistics(final_costs, 'stats.png')

print(f'Optimization completed: Mean={mean:.4f}, StdDev={std:.4f}')
```

## Cost Function Details

### Normalized vs Absolute Cost

**Normalized Cost** (recommended for tracking improvement):
```python
cost = wmi_calculate_cost(
    area, wl, ar,
    init_area=initial_area,
    init_wirelength=initial_wl,
    target_ar=1.0,
    weights=(0.4, 0.4, 0.2)
)
```

**Absolute Cost** (for comparing different initial layouts):
```python
cost = wmi_calculate_cost(
    area, wl, ar,
    init_area=1.0,
    init_wirelength=1.0,
    target_ar=1.0,
    weights=(0.4, 0.4, 0.2)
)
```

## Weight Selection Guidelines

The `weights` tuple `(w₀, w₁, w₂)` controls the importance of each objective:

- **w₀**: Area weight (minimize chip area)
- **w₁**: Wirelength weight (minimize wire length for timing/power)
- **w₂**: Aspect ratio weight (meet manufacturing constraints)

**Common configurations:**
- Balanced: `(0.33, 0.33, 0.34)`
- Area-focused: `(0.6, 0.3, 0.1)`
- Wirelength-focused: `(0.2, 0.7, 0.1)`
- Aspect-ratio-constrained: `(0.3, 0.3, 0.4)`

## Output Files

All plotting functions generate high-resolution (300 DPI) PNG images suitable for publication and reports.

## License

This library is designed for academic and professional EDA research.

## Contributing

This library follows PEP-8 coding standards. All functions use the `wmi_` prefix for namespace consistency.

## Support

For issues or questions, please refer to the function docstrings or the examples provided above.
