import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm


def wmi_calculate_cost(area, wirelength, aspect_ratio, init_area,
                       init_wirelength, target_ar, weights):
    w0, w1, w2 = weights
    cost = (w0 * (area / init_area) +
            w1 * (wirelength / init_wirelength) +
            w2 * (aspect_ratio - target_ar) ** 2)
    return float(cost)


def wmi_log_step(log_data, iteration, time_val, cost, area, wirelength,
                 aspect_ratio):
    log_entry = {
        'Iteration': iteration,
        'Time': time_val,
        'Cost': cost,
        'Area': area,
        'Wirelength': wirelength,
        'AspectRatio': aspect_ratio
    }
    log_data.append(log_entry)
    return log_data


def wmi_save_csv(log_data, filename):
    if not log_data:
        return
    
    fieldnames = log_data[0].keys()
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_data)


def wmi_plot_convergence(log_data, output_filename):
    times = [entry['Time'] for entry in log_data]
    costs = [entry['Cost'] for entry in log_data]
    
    plt.figure(figsize=(10, 6))
    plt.plot(times, costs, linewidth=2, color='blue')
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Cost', fontsize=12)
    plt.title('Optimization Convergence', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()


def wmi_plot_trajectory(log_data, output_filename):
    areas = [entry['Area'] for entry in log_data]
    wirelengths = [entry['Wirelength'] for entry in log_data]
    iterations = np.arange(len(log_data))
    
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(areas, wirelengths, c=iterations,
                         cmap='coolwarm', s=50, alpha=0.7)
    plt.colorbar(scatter, label='Iteration')
    plt.xlabel('Area', fontsize=12)
    plt.ylabel('Wirelength', fontsize=12)
    plt.title('Optimization Trajectory', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()


def wmi_analyze_statistics(final_results_list, output_filename):
    data = np.array(final_results_list)
    mean_val = np.mean(data)
    std_val = np.std(data, ddof=1)
    
    plt.figure(figsize=(10, 6))
    
    counts, bins, patches = plt.hist(data, bins=20, density=True,
                                     alpha=0.7, color='skyblue',
                                     edgecolor='black')
    
    x_range = np.linspace(data.min(), data.max(), 100)
    gaussian_fit = norm.pdf(x_range, mean_val, std_val)
    plt.plot(x_range, gaussian_fit, 'r-', linewidth=2,
             label=f'Gaussian Fit\nμ={mean_val:.4f}, σ={std_val:.4f}')
    
    plt.xlabel('Final Cost', fontsize=12)
    plt.ylabel('Probability Density', fontsize=12)
    plt.title('Statistical Analysis of Final Results', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()
    
    return mean_val, std_val


def wmi_compare_methods(method_logs, method_names, output_filename):
    plt.figure(figsize=(12, 6))
    
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown']
    
    for idx, (log_data, name) in enumerate(zip(method_logs, method_names)):
        times = [entry['Time'] for entry in log_data]
        costs = [entry['Cost'] for entry in log_data]
        color = colors[idx % len(colors)]
        plt.plot(times, costs, linewidth=2, label=name, color=color)
    
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Cost', fontsize=12)
    plt.title('Method Comparison', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()
