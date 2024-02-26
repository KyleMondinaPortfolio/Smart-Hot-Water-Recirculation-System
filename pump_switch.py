import utils
import datetime
import time
from gpiozero import LED

config = utils.load_config("config.json")
HW_LED_PIN = config["HW_LED_PIN"]
PUMP_SWITCH_INTV = config["PUMP_SWITCH_INTV"]
pump_status = LED(HW_LED_PIN)

def pump_switch(hw_forecast):
    while True:
        now = datetime.datetime.now()
        index = ((now.hour * 60) + now.minute) // 5 + 1
        global hw_forecast
        is_hw_needed = hw_forecast[index]

        if(is_hw_needed):
            pump_status.on()
        else:
            pump_status.off()
        time.sleep(PUMP_SWITCH_INTV)



