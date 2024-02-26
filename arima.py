import global_vars
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

def predict_by_arima():

    while True:
        current_time = datetime.datetime.now().time()
        # Check if current time is the schedule time to run the prediction
        if current_time.hour == PREDICTION_SCHEDULE and current_time.minute == 0:
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
                    file.write(str(forecast_value) + '\n')

            # Wait for the next day
            next_day = datetime.datetime.now() + datetime.timedelta(days=1)
            next_day = next_day.replace(hour = PREDICTION_SCHEDULE, minute = 0, second = 0, microsecond = 0)
            time_to_sleep = (next_day - datetime.datetime.now()).total_seconds()
            time.sleep(time_to_sleep)
        else:
            time.sleep(60)

