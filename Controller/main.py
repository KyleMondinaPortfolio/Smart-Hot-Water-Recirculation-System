import schedule
import time
import numpy as np
from arima import predict_by_arima
from pump_controller import control_pump

hot_water_forecast = np.loadtxt('HotWaterForecast.csv', delimiter=',')
water_status = 0

schedule.every(30).minutes.do(control_pump, hot_water_forecast=hot_water_forecast, water_status=water_status)
schedule.every().day.at("02:00").do(arima)

while True:
    schedule.run_pending()
    time.sleep(1)