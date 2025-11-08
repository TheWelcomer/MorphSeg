import torch
import torch.nn as nn

from abc import ABC
from torch import Tensor
from util import make_mask_3d


class Attention(nn.Module, ABC):
    def _get_raw_attention_scores(self, queries: Tensor, keys: Tensor) -> Tensor:
        raise NotImplementedError

    def forward(self, queries: Tensor, keys: Tensor, query_lengths: Tensor, key_lengths: Tensor) -> Tensor:
        mask = make_mask_3d(query_lengths, key_lengths)
        mask = mask.to(queries.device)

        attention_scores = self._get_raw_attention_scores(queries, keys)
        attention_scores = torch.masked_fill(attention_scores, mask=mask, value=-torch.inf)
        attention_scores = torch.softmax(attention_scores, dim=-1)
        attention_scores = torch.masked_fill(attention_scores, mask=mask, value=0.0)

        context_vectors = torch.bmm(attention_scores, keys)
        return context_vectors


class DotProductAttention(Attention):
    def _get_raw_attention_scores(self, queries: Tensor, keys: Tensor) -> Tensor:
        return torch.bmm(queries, keys.transpose(1, 2))


class MLPAttention(Attention):
    def __init__(self, query_size: int, key_size: int, hidden_size: int, dropout: float = 0.0):
        super(MLPAttention, self).__init__()

        self.query_size = query_size
        self.key_size = key_size
        self.hidden_size = hidden_size
        self.dropout = dropout

        self.attention_mlp = nn.Sequential(
                nn.Dropout(p=dropout),
                nn.Linear(query_size + key_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, 1)
            )

    def _get_raw_attention_scores(self, queries: Tensor, keys: Tensor) -> Tensor:
        batch_size = queries.shape[0]
        timesteps_queries = queries.shape[1]
        timesteps_keys = keys.shape[1]

        queries = queries.unsqueeze(2).expand((batch_size, timesteps_queries, timesteps_keys, self.query_size))
        keys = keys.unsqueeze(2).expand((batch_size, timesteps_keys, timesteps_queries, self.key_size))
        keys = keys.transpose(1, 2)
        attention_mlp_inputs = torch.cat([keys, queries], dim=-1)
        attention_scores = self.attention_mlp(attention_mlp_inputs)
        attention_scores = attention_scores.squeeze(dim=-1)

        return attention_scores
