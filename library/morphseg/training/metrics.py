import numpy as np
import editdistance

from typing import List
from typing import Optional
from collections import namedtuple

metric_names = ["loss", "wer", "ter", "edit_distance", "normalised_edit_distance"]
Metrics = namedtuple(
    "Metrics", field_names=metric_names
)


def get_metrics(predictions: List[List[str]], targets: List[List[str]],
                losses: Optional[List[float]] = None) -> Metrics:
    assert len(predictions) == len(targets)
    assert len(predictions) > 0

    num_correct_sequences = 0
    total_num_sequences = 0
    num_correct_tokens = 0
    total_num_tokens = 0

    edit_distances = []
    normalised_edit_distances = []

    for predicted_symbols, target_symbols in zip(predictions, targets):
        total_num_sequences += 1

        # WER / Sequence Accuracy
        if predicted_symbols == target_symbols:
            num_correct_sequences += 1

        # Token Accuracy
        if len(predicted_symbols) != len(target_symbols):
            num_correct_tokens = np.nan  # Can't calculate token accuracy for sequences with unequal number of symbols

        for predicted_symbol, target_symbol in zip(predicted_symbols, target_symbols):
            num_correct_tokens += (predicted_symbol == target_symbol)
            total_num_tokens += 1

        # (Normalised) Edit Distance
        dist = editdistance.distance(predicted_symbols, target_symbols)
        edit_distances.append(dist)
        normalised_edit_distances.append(dist / len(target_symbols))

    wer = 100 * (1 - num_correct_sequences / total_num_sequences)
    ter = 100 * (1 - num_correct_tokens / total_num_tokens) if total_num_tokens > 0 else None
    loss = np.mean(losses) if losses is not None else None

    return Metrics(
        loss=loss,
        wer=wer,
        ter=ter,
        edit_distance=np.mean(edit_distances),
        normalised_edit_distance=np.mean(normalised_edit_distances)
    )
