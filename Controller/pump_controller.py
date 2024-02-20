import numpy as np

def control_pump:
    
    current_value = hot_water_forecast[0]
    
    if water_status == 0 and current_value = 1:
        print("Turning water ON")
        water_status = 1
    elif water_status == 1 and current_value == 0:
        # Water is on, but the current value is 0, so turn it off
        print("Turning water OFF.")
        water_status = 0
    else:
        # Water status is already in the desired state, no action is needed
        print("Water status is unchanged.")
        
    hot_water_forecast = np.delete(hot_water_forecast, 0)
