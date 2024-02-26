import utils
import datetime
import time
import threading
from gpiozero import LED

config = utils.load_config("config.json")
HW_LED_PIN = config["HW_LED_PIN"]
PUMP_SWITCH_INTV = config["PUMP_SWITCH_INTV"]
PREDICTION_SCHEDULE = config["PREDICTION_SCHEDULE"]

pump_status = LED(HW_LED_PIN)
hw_forecast = utils.load_hw_forecast("hw_forecast.txt")

hw_demands_lock = threading.Lock()
hw_forecast_lock = threading.Lock()
