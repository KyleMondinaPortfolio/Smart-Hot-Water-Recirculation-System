import json
from datetime import datetime, timedelta
import pandas as pd

def load_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
    return config

def load_hw_forecast(hw_forecast_file):
    with open(hw_forecast_file, "r") as f:
        return [int(line.strip()) for line in f]

# Function to convert time to 30-minute intervals starting from 12:00am
def time_to_index(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M:%S")  # Updated format string
    minutes_since_midnight = (time_obj - time_obj.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60
    return int(minutes_since_midnight // 30)


# Given the file for hot water detection results, preprocess the data suitable for arima prediction function
def preprocess_for_arima(file):
    # Read the lines from the txt file
    with open(file, 'r') as file:
        lines = file.readlines()

    # Create a dictionary to store the data
    data = {}

    # Parse the lines and fill the dictionary
    for line in lines:
        values = line.split()
        hot_water_needed = int(values[0])
        date = values[1]
        time = values[2][:8]  # Extract only the HH:MM:SS part

        index = (date, time_to_index(time))
        if index not in data:
            data[index] = hot_water_needed
        else:
            data[index] |= hot_water_needed

    # Find the range of dates and times
    dates = sorted(set(date for date, _ in data.keys()))
    times = sorted(set(index[1] for index in data.keys()))

    # Create the 2D array
    today_array = [[data.get((date, time), 0) for time in times] for date in dates]

    df = pd.DataFrame(today_array)
    return df.T