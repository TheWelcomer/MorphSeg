import torch
import torch.nn as nn


class ExpansionLayer(nn.Module):
    def __init__(self, input_size: int, tau: int, dropout: float = 0.0):
        super(ExpansionLayer, self).__init__()
        self.input_size = input_size
        self.tau = tau
        self.dropout = dropout

        self.expansion_layer = nn.Sequential(
            nn.Dropout(p=self.dropout),
            nn.Linear(input_size, self.tau * input_size)
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        # Get tensor shape after expansion
        expanded_shape = list(inputs.shape)
        expanded_shape[-2] = expanded_shape[-2] * self.tau

        expanded_inputs = self.expansion_layer(inputs)
        expanded_inputs = torch.reshape(input=expanded_inputs, shape=expanded_shape)
        return expanded_inputs
