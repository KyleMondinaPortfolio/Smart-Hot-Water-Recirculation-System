# import necessary packages
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
 
dfSample0 =  pd.read_csv('../data/new/sample-5.csv')

arrSample = dfSample0.iloc[:,0]
arrSampley = dfSample0.iloc[:,1]
arrSamplez = dfSample0.iloc[:,2]


stockValuesArraySample = pd.DataFrame(
    {'values': arrSample})
stockValuesArraySampley = pd.DataFrame(
    {'values': arrSampley})
stockValuesArraySamplez = pd.DataFrame(
    {'values': arrSamplez})


# finding EMA for x
emaShower = stockValuesArraySampley.ewm(com=0.4).mean()

# print(emaShowery)
print(emaShower.mean());
print(emaShower.max());


# Define the signal array (example)
signal = emaShower.max()['values'];

# Define thresholds for on and off states
on_threshold_low = 0.1
on_threshold_high = 0.25
off_threshold_low = 0.15
off_threshold_high = 0.20

# Initialize a list to store the state of each value in the signal
signal_states = []

if off_threshold_low <= signal <= off_threshold_high:
    signal_states.append("off")
elif on_threshold_low <= signal <= on_threshold_high:
    signal_states.append("on")
else:
    signal_states.append("unknown")

# Print the state of each value in the signal
for idx, state in enumerate(signal_states):
    print(f"Value at index {idx}: State: {state}")

