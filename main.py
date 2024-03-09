from global_vars import hw_forecast_lock, hw_forecast, pump_status, PUMP_SWITCH_INTV
import datetime
import threading
import time
from arima import predict_by_arima

def pump_switch():
    while True:
        now = datetime.datetime.now()
        index = ((now.hour * 60) + now.minute) // 30
        with hw_forecast_lock:
            is_hw_needed = hw_forecast[index]

        if(is_hw_needed):
            pump_status.on()
        else:
            pump_status.off()
        time.sleep(PUMP_SWITCH_INTV)

def main():
    thread1 = threading.Thread(target=predict_by_arima)
    thread2 = threading.Thread(target=pump_switch)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

if __name__ == "__main__":
    main()
