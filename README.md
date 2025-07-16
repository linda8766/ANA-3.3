import pandas as pd
from datetime import datetime

# Sample function to perform MIP 3.3 Contemporaneous As-Is Analysis
def mip_33_analysis(schedule_data, update_dates):
    """
    Perform MIP 3.3 Observational / Dynamic / Contemporaneous As-Is analysis.
    
    Parameters:
    - schedule_data: DataFrame with columns ['ActivityID', 'UpdateDate', 'StartDate', 'EndDate', 'Duration', 'Critical']
    - update_dates: List of schedule update dates to define analysis windows
    
    Returns:
    - Dictionary with delay analysis results for each window
    """
    results = {}
    
    # Convert date columns to datetime
    schedule_data['UpdateDate'] = pd.to_datetime(schedule_data['UpdateDate'])
    schedule_data['StartDate'] = pd.to_datetime(schedule_data['StartDate'])
    schedule_data['EndDate'] = pd.to_datetime(schedule_data['EndDate'])
    
    # Sort update dates
    update_dates = sorted([pd.to_datetime(date) for date in update_dates])
    
    # Analyze each window (between consecutive update dates)
    for i in range(len(update_dates) - 1):
        start_window = update_dates[i]
        end_window = update_dates[i + 1]
        window_key = f"Window_{start_window.date()}_to_{end_window.date()}"
        results[window_key] = {}
        
        # Filter data for the current window
        window_data_start = schedule_data[schedule_data['UpdateDate'] == start_window]
        window_data_end = schedule_data[schedule_data['UpdateDate'] == end_window]
        
        # Identify critical activities in each update
        critical_start = window_data_start[window_data_start['Critical'] == True]
        critical_end = window_data_end[window_data_end['Critical'] == True]
        
        # Calculate project completion date for each update
        completion_start = critical_start['EndDate'].max()
        completion_end = critical_end['EndDate'].max()
        
        # Calculate delay in the window (in days)
        if completion_start and completion_end:
            delay = (completion_end - completion_start).days
        else:
            delay = 0
        
        # Store results
        results[window_key]['Delay'] = delay
        results[window_key]['CriticalActivitiesStart'] = critical_start['ActivityID'].tolist()
        results[window_key]['CriticalActivitiesEnd'] = critical_end['ActivityID'].tolist()
        results[window_key]['CompletionStart'] = completion_start
        results[window_key]['CompletionEnd'] = completion_end
        
        # Identify critical path shifts (activities that became critical)
        new_critical = set(critical_end['ActivityID']) - set(critical_start['ActivityID'])
        results[window_key]['CriticalPathShifts'] = list(new_critical)
    
    return results

# Example usage
# Sample data (replace with actual schedule data)
data = {
    'ActivityID': ['A1', 'A2', 'A3', 'A1', 'A2', 'A3'],
    'UpdateDate': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-02-01', '2023-02-01', '2023-02-01'],
    'StartDate': ['2023-01-01', '2023-01-10', '2023-01-20', '2023-01-01', '2023-01-15', '2023-01-25'],
    'EndDate': ['2023-01-10', '2023-01-20', '2023-02-01', '2023-01-10', '2023-01-25', '2023-02-10'],
    'Duration': [10, 10, 12, 10, 10, 16],
    'Critical': [True, False, True, True, True, False]
}
schedule_df = pd.DataFrame(data)
update_dates = ['2023-01-01', '2023-02-01']

# Run MIP 3.3 analysis
results = mip_33_analysis(schedule_df, update_dates)

# Print results
for window, details in results.items():
    print(f"\n{window}:")
    print(f"Delay: {details['Delay']} days")
    print(f"Critical Activities (Start): {details['CriticalActivitiesStart']}")
    print(f"Critical Activities (End): {details['CriticalActivitiesEnd']}")
    print(f"Completion Date (Start): {details['CompletionStart']}")
    print(f"Completion Date (End): {details['CompletionEnd']}")
    print(f"Critical Path Shifts: {details['CriticalPathShifts']}")
