import numpy as np
from statsmodels.tsa.arima.model import ARIMA

def predict_by_arima():
    data = np.loadtxt('HotWaterDemand.csv', delimiter=',')
    day_vs_hour = data.T
    next_day_forecast = np.array([])
    
    for hour in day_vs_hour:
        p=2
        q=1
        model = ARIMA(hour, order=(p,1,q))
        arma_model = model.fit()
        forecast = arma_model.forecast(steps=1)
        next_day_forecast = np.append(next_day_forecast,forecast[0])
    
    np.savetxt('HotWaterForecast.csv', next_day_forecast, fmt="%d", delimiter=" ")
    


    