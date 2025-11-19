import torch
import torch.nn as nn

from abc import ABC
from torch import Tensor


class BaseCRF(nn.Module, ABC):
    def __init__(self, num_labels: int):
        super(BaseCRF, self).__init__()
        self.num_labels = num_labels

        self._prior = nn.Parameter(torch.zeros(num_labels))
        self._final_transition_scores = nn.Parameter(torch.zeros(num_labels))

    @property
    def prior(self) -> Tensor:
        return torch.log_softmax(self._prior, dim=-1)

    @property
    def final_transition_scores(self) -> Tensor:
        return torch.log_softmax(self._final_transition_scores, dim=-1)

    @property
    def transition_scores(self) -> Tensor:
        raise NotImplementedError

    def get_transition_scores(self, label_sequences: Tensor) -> Tensor:
        raise NotImplementedError


class CRF(BaseCRF):
    def __init__(self, num_labels: int):
        super(CRF, self).__init__(num_labels=num_labels)
        self._transition_scores = nn.Parameter(torch.zeros(num_labels, num_labels))

    @property
    def transition_scores(self, source_index: Tensor = None, target_index: Tensor = None) -> Tensor:
        if source_index is not None and target_index is not None:
            raise NotImplementedError

        return torch.log_softmax(self._transition_scores, dim=1)

    def get_transition_scores(self, label_sequences: Tensor) -> Tensor:
        return self.transition_scores[label_sequences[:, :-1], label_sequences[:, 1:]]
