
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def segment_gait_cycles(grf_y_column, data, threshold=60):
    """Segment gait cycles based on vertical ground reaction force (GRF) data.
    
    Parameters:
    - grf_y_column: pandas Series with vertical GRF data
    - threshold: force threshold to detect foot contact (default is 60 N)
    - data: optional pandas DataFrames with additional data to segment (e.g. kinematics)
    
    Returns:
    - segments: lists of DataFrames with segmented data if additional_data is provided
    """
    # Make sure to make the time starts at 0 in each returned segment
    v_force = grf_y_column
    is_above = (v_force > threshold).astype(int)

    diff = np.diff(is_above)
    heel_strikes = np.where(diff == 1)[0] 
    cycles = []

    for i in range(len(heel_strikes) - 1):
        start_idx = heel_strikes[i]
        end_idx = heel_strikes[i + 1]

        cycle_df = data.iloc[start_idx:end_idx].copy()
        
        if grf_y_column[start_idx:end_idx].max() >= threshold:
            cycles.append(cycle_df)
        
    if not cycles:
        print("Warning: No gait cycles detected. Please check the threshold and GRF data.")

    durations = [len(cycle) for cycle in cycles]
    mean_duration = np.mean(durations)
    std_duration = np.std(durations)
    lower_bound = mean_duration - 2 * std_duration
    upper_bound = mean_duration + 2 * std_duration

    final_cycles = [c for c in cycles if lower_bound <= len(c) <= upper_bound]

    return final_cycles


def ensemble_average(cycles):
    """Compute the ensemble average and standard deviation of segmented gait cycles.
    
    Parameters:
    - cycles: list of pandas DataFrames, each containing one gait cycle
    
    Returns:
    - mean_cycle: pandas DataFrame with the mean values across all cycles
    - std_cycle: pandas DataFrame with the standard deviation across all cycles
    """
    if len(cycles) == 0:
        return None, None
    
    num_points = 100
    common_x = np.linspace(0, 1, num_points)
    columns = cycles[0].columns
    all_resampled = []

    for cycle in cycles:
        original_x = np.linspace(0, 1, len(cycle))
        resampled_cycle = {}
        for col in columns:
            f = interp1d(original_x, cycle[col].values, kind='linear', fill_value='extrapolate')
            resampled_cycle[col] = f(common_x)
        all_resampled.append(pd.DataFrame(resampled_cycle))
    
    data_3d = np.array([df.values for df in all_resampled])
    mean_array =  np.mean(data_3d, axis=0)
    std_array = np.std(data_3d, axis=0)

    mean_cycle = pd.DataFrame(mean_array, columns=columns)
    std_cycle = pd.DataFrame(std_array, columns=columns)
    if 'time' in mean_cycle.columns:
        mean_cycle['time'] = np.linspace(0, 100, num_points)

    return mean_cycle, std_cycle
