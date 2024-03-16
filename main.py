import utils
import datetime
import time
import threading
import json
from gpiozero import LED
from socketio import Client
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

config = utils.load_config("config.json")
# LED pin to indicate if hot water is recirculating
HW_LED_PIN = config["HW_LED_PIN"]
# Interval in seconds how often to check if the water pump needs to be turned on or not
PUMP_SWITCH_INTV = config["PUMP_SWITCH_INTV"] * 60
# When to run prediction algorithm
PREDICTION_SCHEDULE = config["PREDICTION_SCHEDULE"]
# Web Socket port
WEB_SOCKET_PORT = config["WEB_SOCKET_PORT"]
#pump_status = LED(HW_LED_PIN)
# Hot water forecast for the current day
HOT_WATER_FORECAST_FILE = config["HOT_WATER_FORECAST_FILE"]
HOT_WATER_HISTORY_FILE = config["HOT_WATER_HISTORY_FILE"]
hw_forecast = utils.load_hw_forecast(HOT_WATER_FORECAST_FILE)

hw_demands_lock = threading.Lock()
hw_forecast_lock = threading.Lock()

# State variables:
predictionStatus = 'off' # Should we run prediction services or not
pumpSwitchStatus = 'off' # Is recirculation pump on or off

### WebSocket server URL
WS_SERVER_URL = "ws://localhost:3000"
WS_SERVER_URL = f"ws://localhost:{WEB_SOCKET_PORT}"
sio = Client()

#pump_status = LED(HW_LED_PIN)


### Socket IO functions: fascilitates interprocess communication with local server hosting frontend UI:
## Update our state variables from events in our nodejs server
@sio.on('updatedState')
def on_message(data):
    print('Recieved Updated States:')
    print(data)
    update_state(data)
    if(pumpSwitchStatus == 'on'):
        #pump_status.on()
        print(f"Pump turned on at {datetime.datetime.now()}")
    else:
        #pump_status.off()
        print(f"Pump turned off at {datetime.datetime.now()}")

# Connect and listen for events in our nodejs server
@sio.event
def connect():
    print("Connected to server")
    sio.emit('requestInitialState')

@sio.event
def disconnect():
    print("Disconnected from server")

# Update state variables
def update_state(data):
    global predictionStatus, pumpSwitchStatus
    predictionStatus = data['predictionStatus']
    pumpSwitchStatus = data['pumpSwitchStatus']
    print(f"Updated state: predictionStatus={predictionStatus}, pumpSwitchStatus={pumpSwitchStatus}")

# Function to that runs in an indefinite loop, every PUMP_SWITCH_INTV seconds, check the current forecast if hot water is needed at the current time
def pump_switch():
    global pumpSwitchStatus
    global predictionStatus 
    while True:
        if (predictionStatus == "on"):
            now = datetime.datetime.now()
            index = ((now.hour * 60) + now.minute) // 15
            with hw_forecast_lock:
               is_hw_needed = hw_forecast[index]
            if is_hw_needed:
                pumpSwitchStatus = 'on'
                sio.emit('pythonUpdate', {'predictionStatus': predictionStatus, 'pumpSwitchStatus': 'on'})
            else:
                pumpSwitchStatus = 'off'
                sio.emit('pythonUpdate', {'predictionStatus': predictionStatus, 'pumpSwitchStatus': 'off'})
        else:
            # Prediction services disabled, pump switch should do nothing
            pass
        time.sleep(PUMP_SWITCH_INTV)

# Prediction algorithm, run every day at the set schedule in config.json, reading the hot water demand history, generate forecast for the next day of the hot water demand
def predict_by_arima():
    global predictionStatus
    while True:
        current_time = datetime.datetime.now().time()
        # Check if current time is the schedule time to run the prediction
        if current_time.hour == PREDICTION_SCHEDULE and current_time.minute == 0:
            if (predictionStatus == "on"):
                print("Running Prediction")
                next_day_forecast = np.array([])
                day_vs_hour = utils.preprocess_for_arima(HOT_WATER_HISTORY_FILE)

                for hour in day_vs_hour.values:
                    p=2
                    q=1
                    model = ARIMA(hour, order=(p,1,q))
                    arma_model = model.fit()
                    forecast = arma_model.forecast(steps=1)
                    next_day_forecast = np.append(next_day_forecast,forecast[0])
                with open(HOT_WATER_FORECAST_FILE, 'w') as output_file:
                    for forecast_value in next_day_forecast:
                        # Convert the forecast value to a floating-point number
                        number = float(forecast_value)

                        # Round the number to either 0 or 1
                        rounded_number = round(number)

                        # Write the rounded value to the output file
                        output_file.write(str(rounded_number) + '\n')

                # Wait for the next day
                next_day = datetime.datetime.now() + datetime.timedelta(days=1)
                next_day = next_day.replace(hour = PREDICTION_SCHEDULE, minute = 0, second = 0, microsecond = 0)
                time_to_sleep = (next_day - datetime.datetime.now()).total_seconds()
                time.sleep(time_to_sleep)
        else:
            # Sleep for a minute
            time.sleep(59)

def main():
    # Connect to the server hosting the frontend UI
    sio.connect(WS_SERVER_URL)

    thread1 = threading.Thread(target=predict_by_arima)
    thread2 = threading.Thread(target=pump_switch) 
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    sio.wait()


if __name__ == "__main__":
    main()
