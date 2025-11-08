import torch
import torch.nn as nn

from torch import Tensor
from util import make_mask_2d
from model.lstm import BiLSTMEncoder
from model.attention import MLPAttention
from model.attention import DotProductAttention


def _mask_sequences_for_pooling(sequences: Tensor, lengths: Tensor, value: float) -> Tensor:
    lengths = torch.clamp(lengths, min=1)
    mask = make_mask_2d(lengths)
    mask = mask.unsqueeze(2).expand(sequences.shape)
    mask = mask.to(sequences.device)
    sequences = torch.masked_fill(sequences, mask=mask, value=value)
    return sequences


def _max_over_time_pooling(sequences: Tensor, lengths: Tensor) -> Tensor:
    sequences = _mask_sequences_for_pooling(sequences, lengths, value=-torch.inf)
    pooled = torch.max(sequences, dim=1).values

    return pooled


def _sum_over_time_pooling(sequences: Tensor, lengths: Tensor) -> Tensor:
    sequences = _mask_sequences_for_pooling(sequences, lengths, value=0.0)
    pooled = torch.sum(sequences, dim=1)

    return pooled


def _mean_over_time_pooling(sequences: Tensor, lengths: Tensor) -> Tensor:
    sum_pooled = _sum_over_time_pooling(sequences, lengths)
    length_normaliser = lengths.float().reshape(len(lengths), 1).expand(sum_pooled.shape).to(sum_pooled.device)
    pooled = sum_pooled / length_normaliser

    return pooled


class Pooling(nn.Module):
    def __init__(self, pooling_type: str):
        super(Pooling, self).__init__()
        self.pooling_type = pooling_type
        assert pooling_type in ["max", "sum", "mean"]

    def forward(self, feature_encodings: Tensor, feature_lengths: Tensor) -> Tensor:
        if self.pooling_type == "max":
            return _max_over_time_pooling(feature_encodings, feature_lengths)
        elif self.pooling_type == "sum":
            return _sum_over_time_pooling(feature_encodings, feature_lengths)
        elif self.pooling_type == "mean":
            return _mean_over_time_pooling(feature_encodings, feature_lengths)
        else:
            raise ValueError(f"Unknown pooling: {self.pooling_type}")


class FeatureEncoder(nn.Module):
    def __init__(self, vocab_size: int, embedding_size: int, hidden_size: int, num_layers: int, dropout: float,
                 pooling: str, context_dim: int, device: torch.device = torch.device("cpu")):
        super(FeatureEncoder, self).__init__()

        self.vocab_size = vocab_size
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.pooling_name = pooling
        self.context_dim = context_dim
        self.device = device

        # Make embedder
        self.embedder = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_size, padding_idx=0)

        # Make encoder
        if num_layers > 0:
            self.encoder = BiLSTMEncoder(
                input_size=embedding_size, hidden_size=hidden_size, dropout=dropout, num_layers=num_layers
            )
        else:
            self.encoder = nn.Linear(embedding_size, hidden_size)

        # Make pooling layer
        if self.pooling_name in ["max", "mean", "sum"]:
            self.pooling = Pooling(pooling_type=pooling)
        elif self.pooling_name == 'dot':
            self.pooling = DotProductAttention()
        elif self.pooling_name == "mlp":
            self.pooling = MLPAttention(
                query_size=context_dim, key_size=hidden_size, dropout=dropout, hidden_size=hidden_size
            )
        else:
            raise ValueError(f"Unknown pooling: {self.pooling_name}")

        # Make final projection
        self.final_projection = nn.Sequential(
            nn.Dropout(p=self.dropout),
            nn.Linear(self.hidden_size + self.context_dim, self.context_dim),
            nn.GELU(),
            nn.Dropout(p=self.dropout),
            nn.Linear(self.context_dim, self.context_dim),
            nn.GELU()
        )

    def _embed_and_encode_features(self, features: Tensor, feature_lengths: Tensor) -> Tensor:
        embedded_features = self.embedder(features.to(self.device))
        if self.num_layers > 0:
            encoded_features = self.encoder(embedded_features, feature_lengths)
        else:
            encoded_features = self.encoder(embedded_features)

        return encoded_features

    def _timewise_pooling(self, encoded_features: Tensor, feature_lengths: Tensor, contexts: Tensor) -> Tensor:
        pooled_features = self.pooling(encoded_features, feature_lengths)
        pooled_features = pooled_features.unsqueeze(1)
        pooled_features = pooled_features.expand(
            (pooled_features.shape[0], contexts.shape[1], pooled_features.shape[2])
        )
        return pooled_features

    def _attention_pooling(self, encoded_features: Tensor, feature_lengths: Tensor, contexts: Tensor) -> Tensor:
        batch, num_contexts_per_batch = contexts.shape[0], contexts.shape[1]
        num_features = encoded_features.shape[1]

        encoded_features = encoded_features.unsqueeze(1)
        encoded_features = encoded_features.expand(
            (batch, num_contexts_per_batch, num_features, encoded_features.shape[3])
        )
        encoded_features = encoded_features.reshape(-1, num_features, encoded_features.shape[3])
        feature_lengths = feature_lengths.unsqueeze(1)
        feature_lengths = feature_lengths.expand((batch, num_contexts_per_batch))
        feature_lengths = feature_lengths.flatten()

        contexts = contexts.reshape(-1, 1, contexts.shape[-1])
        context_lengths = torch.ones(batch * num_contexts_per_batch, dtype=torch.long)

        pooled_features = self.pooling(
            queries=contexts, query_lengths=context_lengths, keys=encoded_features, key_lengths=feature_lengths
        )
        pooled_features = pooled_features.reshape(batch, num_contexts_per_batch, encoded_features.shape[-1])
        return pooled_features

    def forward(self, features: Tensor, feature_lengths: Tensor, contexts: Tensor) -> Tensor:
        encoded_features = self._embed_and_encode_features(features, feature_lengths)
        # encoded_features: shape batch x #features x hidden
        # contexts: shape batch x #contexts x hidden

        if self.pooling_name in ["max", "mean", "sum"]:
            pooled = self._timewise_pooling(encoded_features, feature_lengths, contexts)
        else:
            pooled = self._attention_pooling(encoded_features, feature_lengths, contexts)

        return self.final_projection(torch.cat([pooled, contexts], dim=-1))
