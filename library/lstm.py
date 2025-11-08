import torch
import torch.nn as nn

from torch.nn.utils.rnn import pad_packed_sequence
from torch.nn.utils.rnn import pack_padded_sequence


class BiLSTMEncoder(nn.Module):
    """
    Implements a wrapper around pytorch's LSTM for easier sequence processing.
    Note: This implementation uses trainable initialisations of hidden states, if they are not provided.
    Note: This implementation projects the combined hidden states of the forward and backward LSTMs to the common
          hidden dimension
    """
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0):
        super(BiLSTMEncoder, self).__init__()

        # Save arguments
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout

        # Make properties
        self._output_size = 2 * self.hidden_size

        # Initialise modules
        self.lstm = nn.LSTM(
            input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True,
            bidirectional=True, dropout=dropout
        )
        self.reduce_dim = nn.Linear(2 * self.hidden_size, self.hidden_size)

        # Initialise trainable hidden state initialisations
        self.h_0 = nn.Parameter(torch.zeros(2 * self.num_layers, 1, self.hidden_size))
        self.c_0 = nn.Parameter(torch.zeros(2 * self.num_layers, 1, self.hidden_size))

    def forward(self, inputs: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        batch_size = len(lengths)

        # Pack sequence
        lengths = torch.clamp(lengths, 1)  # Enforce all lengths are >= 1 (required by pytorch)
        inputs = pack_padded_sequence(inputs, lengths, batch_first=True, enforce_sorted=False)

        # Prepare hidden states
        h_0 = self.h_0.tile((1, batch_size, 1))
        c_0 = self.c_0.tile((1, batch_size, 1))

        # Apply LSTM
        encoded, _ = self.lstm(inputs, (h_0, c_0))
        encoded, _ = pad_packed_sequence(encoded, batch_first=True)

        # Project down
        encoded = self.reduce_dim(encoded)

        return encoded
