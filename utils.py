import json

from datetime import datetime, timedelta
import pandas as pd
import csv
config = load_config("config.json")
PUMP_SWITCH_INTV = config["PUMP_SWITCH_INTV"]


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
    return int(minutes_since_midnight // PUMP_SWITCH_INTV)


# Given the file for hot water detection results, preprocess the data suitable for arima prediction function

def preprocess_for_arima(file):

    # Create a dictionary to store the data
    data = {}

    with open(file, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            try:
                value = int(row[0])
            except ValueError:
                print("Invalid value:", row[0])
                continue

            hot_water_needed = int(row[0])
            date_time_str = row[1]
            date_time_str = date_time_str.strip("{}").split("(")[1].split(")")[0]
            date_time_obj = datetime.strptime(date_time_str, "%Y, %m, %d, %H, %M, %S, %f")

            date = date_time_obj.date()
            time = date_time_obj.strftime("%H:%M:%S")

            index = (date, time_to_index(time))
            if index not in data:
                data[index] = hot_water_needed
            else:
                data[index] |= hot_water_needed

    # Find the range of dates and times
    dates = sorted(set(date for date, _ in data.keys()))
    times = [i for i in range(0,  1440 /  PUMP_SWITCH_INTV)]

    # Create the 2D array
    today_array = [[data.get((date, time), 0) for time in times] for date in dates]
    print(today_array)
    df = pd.DataFrame(today_array)
    return df.T
