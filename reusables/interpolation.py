import numpy as np

# Given a varying array length, convert to an array of length N through linear interpolation
# Plot the array on a graph, for the x axis it spans, divide into N sections
# the y values of each of the N parts form an array of length N 
def linear_interpolation(arr, N): 
    arr = np.asarray(arr, dtype=float)
    old_N = len(arr) 

    # base case: N = 0 
    if old_N == 0: 
        raise ValueError("Array of length 0 passed to linear interpolation")
    if old_N == 1: 
        return [arr[0]]*N 

    x_old = np.linspace(0, 1, old_N)
    x_new = np.linspace(0, 1, N)

    return np.interp(x_new, x_old, arr).tolist() 

# Given an array in the form of [{metrics}, {metrics}], 
# linearly interpolate all metrics 
def linear_interpolation_metrics(metrics_arr, N): 
    pass 