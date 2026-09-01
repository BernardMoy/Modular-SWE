import numpy as np
from collections import defaultdict


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
        return [arr[0]] * N

    x_old = np.linspace(0, 1, old_N)
    x_new = np.linspace(0, 1, N)

    return np.interp(x_new, x_old, arr).tolist()


# Given an array in the form of [{metrics}, {metrics}] coorresponding to the eval metrics columns,
# linearly interpolate all metrics into [{m}, {m}, ...] of length N 
def linear_interpolation_metrics(metrics_arr, N):
    result = defaultdict(list)

    for metrics in metrics_arr:
        for key, value in metrics.items():
            # SKIP these two fields 
            if key in ["implementation_path", "has_cycles"]:
                continue
            result[key].append(value)

    # for all the value arrays inside result, linear interpolate them
    for key, value in result.items():
        result[key] = linear_interpolation(value, N)

    # re-assign interpolated values using result[key][i]
    new_metrics_arr = [
        {key: result[key][i] for key in result} for i in range(N)
    ]

    # implementation path (containing version numbers), and has_cycles, cannot be interpolated. 

    return new_metrics_arr
