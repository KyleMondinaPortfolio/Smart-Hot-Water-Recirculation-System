import utils

test = utils.preprocess_for_arima('sample-data-8.txt')
print(test)

data_array = test.values.flatten()

# Write each element to a line in a file
with open('ground_truth.txt', 'w') as file:
    for item in data_array:
        file.write(str(item) + '\n')

# Optional: Print the array
print(data_array)

