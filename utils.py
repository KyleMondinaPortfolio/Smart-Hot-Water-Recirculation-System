import json

def load_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
    return config

def load_hw_forecast(hw_forecast_file):
    with open(hw_forecast_file, "r") as f:
        return [int(line.strip()) for line in f]