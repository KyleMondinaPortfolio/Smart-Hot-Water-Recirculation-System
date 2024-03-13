import numpy as np
import datetime
import time
from statsmodels.tsa.arima.model import ARIMA
import utils

def predict_by_arima():

    next_day_forecast = np.array([])
    day_vs_hour = utils.preprocess_for_arima('sample-data-4-7.txt')

    for hour in day_vs_hour.values:
        p=1
        q=1
        model = ARIMA(hour, order=(p,1,q))
        arma_model = model.fit()
        forecast = arma_model.forecast(steps=1)
        next_day_forecast = np.append(next_day_forecast,forecast[0])
    with open('rounded_output.txt', 'w') as output_file:
        for forecast_value in next_day_forecast:
            # Convert the forecast value to a floating-point number
            number = float(forecast_value)

            # Round the number to either 0 or 1
            rounded_number = round(number)

            # Write the rounded value to the output file
            output_file.write(str(rounded_number) + '\n')

predict_by_arima()

