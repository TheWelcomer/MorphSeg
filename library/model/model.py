import torch
import torch.nn as nn

from torch import Tensor
from model.crf import CRF
from typing import Optional
from model.lstm import BiLSTMEncoder
from model.feature_encoder import FeatureEncoder
from model.expansion_layer import ExpansionLayer


class LSTMModel(nn.Module):
    def __init__(self, vocab_size: int, num_labels: int, device: torch.device, embedding_size: int = 64,
                 hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0, tau: int = 2,
                 use_crf: bool = False, use_features: bool = False, feature_embedding_size: int = 32,
                 feature_hidden_size: int = 128, feature_num_layers: int = 0, feature_pooling: str = "mean"):
        super(LSTMModel, self).__init__()
        self.vocab_size = vocab_size
        self.num_labels = num_labels
        self.device = device
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.tau = tau
        self.use_crf = use_crf
        self.use_features = use_features
        self.feature_embedding_size = feature_embedding_size
        self.feature_hidden_size = feature_hidden_size
        self.feature_num_layers = feature_num_layers
        self.feature_pooling = feature_pooling

        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_size, padding_idx=0)
        self.encoder = BiLSTMEncoder(
            input_size=embedding_size, num_layers=num_layers, hidden_size=hidden_size, dropout=dropout
        )

        if self.tau > 1:
            self.expansion_layer = ExpansionLayer(input_size=hidden_size, tau=tau)
        else:
            self.expansion_layer = nn.Identity()

        self.classifier = nn.Sequential(nn.GELU(), nn.Linear(hidden_size, num_labels))

        if self.use_crf:
            self.crf = CRF(num_labels=num_labels)

        if self.use_features:
            self.feature_encoder = FeatureEncoder(
                vocab_size=vocab_size, embedding_size=self.feature_embedding_size, hidden_size=self.feature_hidden_size,
                num_layers=self.feature_num_layers, context_dim=hidden_size, device=self.device, dropout=self.dropout,
                pooling=self.feature_pooling
            )

    def get_params(self):
        return {
            'vocab_size': self.vocab_size,
            'num_labels': self.num_labels,
            'device': self.device,
            'embedding_size': self.embedding_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'dropout': self.dropout,
            'tau': self.tau,
            'use_crf': self.use_crf,
            'use_features': self.use_features,
            'feature_embedding_size': self.feature_embedding_size,
            'feature_hidden_size': self.feature_hidden_size,
            'feature_num_layers': self.feature_num_layers,
            'feature_pooling': self.feature_pooling
        }

    def forward(self, inputs: Tensor, lengths: Tensor, features: Optional[Tensor] = None,
                feature_lengths: Optional[Tensor] = None) -> Tensor:
        embedded = self.embedding(inputs.to(self.device))
        encoded = self.encoder(embedded, lengths)
        if self.use_features:
            encoded = self.feature_encoder(features=features, feature_lengths=feature_lengths, contexts=encoded)

        encoded = self.expansion_layer(encoded)
        logits = self.classifier(encoded)
        return logits
