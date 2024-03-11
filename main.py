import utils
import datetime
import time
import threading
import json
from gpiozero import LED
from socketio import Client

from gpiozero.pins.rpigpio import RPiGPIOFactory

HW_LED_PIN = 17  # Adjust pin number as needed
rpi_gpio_factory = RPiGPIOFactory()
pump_status = LED(HW_LED_PIN)

#from arima import predict_by_arima

config = utils.load_config("config.json")
### LED pin to indicate if hot water is recirculating
#HW_LED_PIN = config["HW_LED_PIN"]
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

### Web Socket:

@sio.on('updatedState')
def on_message(data):
    print('Recieved Updated States:')
    print(data)
    update_state(data)
    if(pumpSwitchStatus == 'on'):
        pump_status.on()
        print('Pump turned on')
    else:
        pump_status.off()
        print('Pump turned off')


@sio.event
def message(data):
    print("hello?")
    print(data)

    # Check if the message contains the updated state
    if 'updatedState' in data:
        updated_state = data['updatedState']
        update_state(updated_state)

    if(predictionStatus):
        pump_status.on()
        print('Pump turned on')
    else:
        pump_status.off()
        print('Pump turned off')

@sio.event
def connect():
    print("Connected to server")
    sio.emit('requestInitialState')

@sio.event
def disconnect():
    print("Disconnected from server")

def update_state(data):
    global predictionStatus, pumpSwitchStatus
    predictionStatus = data['predictionStatus']
    pumpSwitchStatus = data['pumpSwitchStatus']
    print(f"Updated state: predictionStatus={predictionStatus}, pumpSwitchStatus={pumpSwitchStatus}")

def pump_switch():
    global pumpSwitchStatus
    while True:
        print("pump switch turning on")
        now = datetime.datetime.now()
        #index = ((now.hour * 60) + now.minute) // 30
        #with hw_forecast_lock:
            #is_hw_needed = hw_forecast[index]
        is_hw_needed = 1

        if is_hw_needed:
            pumpSwitchStatus = 'on'
            sio.emit('pythonUpdate', {'predictionStatus': pumpSwitchStatus, 'pumpSwitchStatus': 'on'})
        else:
            pumpSwitchStatus = 'off'
            sio.emit('pythonUpdate', {'predictionStatus': pumpSwitchStatus, 'pumpSwitchStatus': 'off'})
        time.sleep(5)


def main():
    sio.connect(WS_SERVER_URL)

    #thread1 = threading.Thread(target=predict_by_arima)
    thread2 = threading.Thread(target=pump_switch)
    #thread1.start()
    thread2.start()
    #thread1.join()
    thread2.join()
    sio.wait()


if __name__ == "__main__":
    main()
