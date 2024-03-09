import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from copy import deepcopy

### ENCODER AND DECODER MODEL CLASSES ###
 
class EncoderRNN(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, device='cpu'):
        super(EncoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.device = device

    def forward(self, input, hidden):
        return self.gru(input, hidden)

    def initHidden(self, batch_size):
        return torch.zeros(1, batch_size, self.hidden_size).to(self.device)


class DecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size, output_seq_len, device):
        super(DecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.output_seq_len = output_seq_len
        self.gru = nn.GRU(hidden_size, hidden_size, batch_first=True)
        self.out = nn.Linear(hidden_size, output_size)
        self.device = device

    def forward(self, input, hidden):
        input = input.repeat(1, self.output_seq_len, 1).to(self.device)
        output, hidden = self.gru(input, hidden)
        output = self.out(output).to(self.device)
        return output, hidden

    def initHidden(self, batch_size):
        return torch.zeros(1, batch_size, self.hidden_size).to(self.device)

### HELPER FUNCTIONS ###

def load_data(device):
    period = 48 - 1 # (sample every 30 min. -> 48 samples per day)
    df = pd.read_csv('data.csv', header=0, usecols=[1]).to_numpy()
    data = torch.tensor(df, dtype=torch.float).to(device)
    return data

def split_data(data):
    # print("\nIn split_data\n")
    num_timesteps = data.shape[0]
    # print("Number of timesteps: ", num_timesteps)
    train_end_indx = round(0.75 * num_timesteps)
    train_data = data[:train_end_indx, :]
    print("Train data shape: ", f"({len(train_data)}, {len(train_data[0])})")
    test_end_indx = train_end_indx + round(0.125 * num_timesteps)
    test_data = data[train_end_indx:test_end_indx, :]
    print("Test data shape: ", f"({len(test_data)}, {len(test_data[0])})")
    val_data = data[test_end_indx:, :]
    print("Val data shape: ", f"({len(val_data)}, {len(val_data[0])})")
    return train_data, val_data, test_data

def create_sequences(data, input_seq_len, output_seq_len):
    input_sequences = []
    target_sequences = []
    for t in range(data.shape[0] - (input_seq_len + output_seq_len) + 1):
        enc_inputs_at_t = deepcopy(data[t : t + input_seq_len, :])
        dec_targets_at_t = deepcopy(data[t + input_seq_len: t + input_seq_len + output_seq_len, :])
        input_sequences.append(enc_inputs_at_t)
        target_sequences.append(dec_targets_at_t)
    input_sequences = torch.stack(input_sequences)
    target_sequences = torch.stack(target_sequences)
    return input_sequences, target_sequences

def train(input, target, encoder: EncoderRNN, decoder: DecoderRNN, encoder_opt, decoder_opt, criterion, hidden_size):
    batch_size = input.size(0)
    encoder_hidden = encoder.initHidden(batch_size)
    decoder.initHidden(batch_size)

    encoder_opt.zero_grad()
    decoder_opt.zero_grad()

    input_length = input.size(1)
    target_length = target.size(1)

    _, encoder_hidden = encoder(input, encoder_hidden)
    decoder_input = torch.zeros(batch_size, 1, hidden_size) # SOS token

    decoder_output, _ = decoder(decoder_input, encoder_hidden)
    decoder_output = decoder_output.transpose(1, 2)
    loss = criterion(decoder_output, target.squeeze(-1).long())
    loss.backward()

    encoder_opt.step()
    decoder_opt.step()

    return loss.item() / target_length

def evaluate_model(encoder, decoder, dataloader, device, hidden_size):
    encoder.eval()
    decoder.eval()
    total_accuracy = 0
    total_count = 0

    with torch.no_grad():
        for input_tensor, target_tensor in dataloader:
            input_tensor, target_tensor = input_tensor.to(device), target_tensor.to(device)
            batch_size = input_tensor.size(0)
            encoder_hidden = encoder.initHidden(batch_size).to(device)

            _, encoder_hidden = encoder(input_tensor, encoder_hidden)
            decoder_input = torch.zeros(batch_size, 1, hidden_size).to(device)
            decoder_output, _ = decoder(decoder_input, encoder_hidden)

            predicted = decoder_output.max(dim=2)[1]
            correct = (predicted == target_tensor.squeeze(-1).int()).sum().item()
            total_accuracy += correct
            total_count += target_tensor.nelement()
        print("predicted: ", predicted[0])
        print("target: ", target_tensor.squeeze(-1)[0])

    return total_accuracy / total_count * 100

def train_models(epochs, train_loader, encoder, decoder, encoder_opt, decoder_opt, criterion, hidden_size):
    best_models = (None, None)
    best_val = float('inf')
    for epoch in range(epochs):
        for _, (input_tensor, target_tensor) in enumerate(train_loader):
            loss = train(input_tensor, target_tensor, encoder, decoder, encoder_opt, decoder_opt, criterion, hidden_size)
        if loss < best_val:
            best_models = (encoder.state_dict(), decoder.state_dict())
        print(f'Epoch: {epoch + 1} \t Loss: {loss:.5f}')
    torch.save(best_models[0], 'models/enc_dummy.pth')
    torch.save(best_models[1], 'models/dec_dummy.pth')

def evaluate_models(test_loader, val_loader, hidden_size, output_length, device):
    encoder = EncoderRNN(input_size=1, hidden_size=hidden_size, device=device)
    encoder_state = torch.load('models/enc_dummy.pth')
    encoder.load_state_dict(encoder_state)
    encoder.to(device)

    decoder = DecoderRNN(hidden_size=hidden_size, output_size=2, output_seq_len=output_length, device=device)
    decoder_state = torch.load('models/dec_dummy.pth')
    decoder.load_state_dict(decoder_state)
    decoder.to(device)

    val_accuracy = evaluate_model(encoder, decoder, test_loader, device, hidden_size)
    test_accuracy = evaluate_model(encoder, decoder, val_loader, device, hidden_size)

    print(f'Test Accuracy: {test_accuracy:.3f}%')
    print(f'Val Accuracy: {val_accuracy:.3f}%')

def _forecast(encoder, decoder, input_tensor, hidden_size, device):
    encoder.eval()
    decoder.eval()

    with torch.no_grad():
        input_tensor = input_tensor.to(device)
        encoder_hidden = encoder.initHidden(1).to(device)
        _, encoder_hidden = encoder(input_tensor, encoder_hidden)
        decoder_input = torch.zeros(1, 1, hidden_size).to(device)
        decoder_output, _ = decoder(decoder_input, encoder_hidden)

        predicted = decoder_output.max(dim=2)[1]
        return predicted

def forecast(historical_data, hidden_size, output_length, device):
    encoder = EncoderRNN(input_size=1, hidden_size=hidden_size, device=device)
    encoder_state = torch.load('models/enc_dummy.pth')
    encoder.load_state_dict(encoder_state)
    encoder.to(device)

    decoder = DecoderRNN(hidden_size=hidden_size, output_size=2, output_seq_len=output_length, device=device)
    decoder_state = torch.load('models/dec_dummy.pth')
    decoder.load_state_dict(decoder_state)
    decoder.to(device)

    predicted_usage = _forecast(encoder, decoder, historical_data, hidden_size, device)
    return predicted_usage

### MAIN LOOP ###
    
'''
    MODE:   train -> trains models from scratch using the data provided in 'data.csv', saves the best models under 'models/'
            eval -> evaluates the most recently saved models, currently achieving 96+% with dummy data (periodic)
            forecast -> forecasts hot water usage for the next day, given an input tensor of historical data, returns prediction
'''

def run(mode, historical_data=None):
    device = 'cpu'
    input_length = 288  # (288 / 48) = 6 days of historical usage
    output_length = 48  # 48 samples => 30 minute sampling intervals; next-day forecast
    batch_size = 64
    hidden_size = 256
    epochs = 10
    lr = 0.00025

    # load the data
    data = load_data(device)
    print("data shape: ", data.shape)

    # split the data into train, val, test
    train_data, val_data, test_data = split_data(data)

    # create input-target sequence pairs
    input_sequences_train, target_sequences_train = create_sequences(train_data, input_length, output_length)
    input_sequences_val, target_sequences_val = create_sequences(val_data, input_length, output_length)
    input_sequences_test, target_sequences_test = create_sequences(test_data, input_length, output_length)

    # convert the data into tensor datasets
    train_dataset = TensorDataset(input_sequences_train, target_sequences_train)
    val_dataset = TensorDataset(input_sequences_val, target_sequences_val)
    test_dataset = TensorDataset(input_sequences_test, target_sequences_test)

    # create data loaders for each dataset
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # initialize models
    encoder = EncoderRNN(input_size=1, hidden_size=hidden_size, device=device).to(device)
    decoder = DecoderRNN(hidden_size=hidden_size, output_size=2, output_seq_len=output_length, device=device).to(device)

    encoder_opt = optim.Adam(encoder.parameters(), lr=lr)
    decoder_opt = optim.Adam(decoder.parameters(), lr=lr)

    class_counts = [38, 10]  # roughly 4:1 ratio of hot water being needed on average in dummy data
    class_weights = torch.tensor([1.0 / x for x in class_counts], device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    if mode == 'train':
        train_models(epochs, train_loader, encoder, decoder, encoder_opt, decoder_opt, criterion, hidden_size)
    if mode == 'eval':
        evaluate_models(test_loader, val_loader, hidden_size, output_length, device)
    if mode == 'forecast':
        return forecast(historical_data, hidden_size, output_length, device)