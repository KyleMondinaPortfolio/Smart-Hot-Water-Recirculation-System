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
### LED pin to indicate if hot water is recirculating
HW_LED_PIN = config["HW_LED_PIN"]
### Interval in seconds how often to check if the water pump needs to be turned on or not
PUMP_SWITCH_INTV = config["PUMP_SWITCH_INTV"]
### When to run prediction algorithm
PREDICTION_SCHEDULE = config["PREDICTION_SCHEDULE"]

### Web Socket port
WEB_SOCKET_PORT = config["WEB_SOCKET_PORT"]

#pump_status = LED(HW_LED_PIN)
### Hot water forecast for the current day
hw_forecast = utils.load_hw_forecast("hw_forecast.txt")

hw_demands_lock = threading.Lock()
hw_forecast_lock = threading.Lock()

# State variables
predictionStatus = 'off'
pumpSwitchStatus = 'off'


### WebSocket server URL
WS_SERVER_URL = "ws://localhost:3000"
sio = Client()

pump_status = LED(HW_LED_PIN)


### Web Socket:

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

#Update state variables
def update_state(data):
    global predictionStatus, pumpSwitchStatus
    predictionStatus = data['predictionStatus']
    pumpSwitchStatus = data['pumpSwitchStatus']
    print(f"Updated state: predictionStatus={predictionStatus}, pumpSwitchStatus={pumpSwitchStatus}")

def pump_switch():
    global pumpSwitchStatus
    global predictionStatus 
    while True:
        if (predictionStatus == "on"):
            now = datetime.datetime.now()
            index = ((now.hour * 60) + now.minute) // 30
            with hw_forecast_lock:
               is_hw_needed = hw_forecast[index]
            if is_hw_needed:
                pumpSwitchStatus = 'on'
                sio.emit('pythonUpdate', {'predictionStatus': pumpSwitchStatus, 'pumpSwitchStatus': 'on'})
            else:
                pumpSwitchStatus = 'off'
                sio.emit('pythonUpdate', {'predictionStatus': pumpSwitchStatus, 'pumpSwitchStatus': 'off'})
        else:
            pass
        time.sleep(PUMP_SWITCH_INTV)

def predict_by_arima():
    global predictionStatus
    while True:
        current_time = datetime.datetime.now().time()
        # Check if current time is the schedule time to run the prediction
        if current_time.hour == PREDICTION_SCHEDULE and current_time.minute == 0:
            if (predictionStatus == "on"):
                print("Running Prediction")
                data = np.loadtxt('hw_demand.csv', delimiter=',')
                day_vs_hour = data.T
                next_day_forecast = np.array([])

                for hour in day_vs_hour:
                    p=2
                    q=1
                    model = ARIMA(hour, order=(p,1,q))
                    arma_model = model.fit()
                    forecast = arma_model.forecast(steps=1)
                    next_day_forecast = np.append(next_day_forecast,forecast[0])
                with open('hw_forecast.txt', 'w') as f:
                    for forecast_value in next_day_forecast:
                        f.write(str(forecast_value) + '\n')

                # Wait for the next day
                next_day = datetime.datetime.now() + datetime.timedelta(days=1)
                next_day = next_day.replace(hour = PREDICTION_SCHEDULE, minute = 0, second = 0, microsecond = 0)
                time_to_sleep = (next_day - datetime.datetime.now()).total_seconds()
                time.sleep(time_to_sleep)
        else:
            # Sleep for a minute
            time.sleep(59)




def main():
    sio.connect(WS_SERVER_URL)

    # Replace target with neural network @Xavier
    thread1 = threading.Thread(target=predict_by_arima)
    thread2 = threading.Thread(target=pump_switch)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    sio.wait()


if __name__ == "__main__":
    main()
