from __future__ import annotations

import torch

from typing import List
from trainer import train
from tqdm.auto import tqdm
from typing import Optional
from settings import Settings
from trainer import load_model
from dataset import RawDataset
from trainer import TrainedModel
from inference import Prediction
from trainer import _get_loss_function
from torch.utils.data import DataLoader
from dataset import SequenceLabellingDataset


class SequenceLabeller:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model: Optional[TrainedModel] = None
        _, self.inference = _get_loss_function(self.settings.loss)

    @classmethod
    def load(cls, path: str) -> SequenceLabeller:
        model = load_model(path=path)
        sequence_labeller = cls(settings=model.settings)
        sequence_labeller.model = model

        return sequence_labeller

    def fit(self, train_data: RawDataset, development_data: Optional[RawDataset] = None) -> SequenceLabeller:
        self.model = train(train_data=train_data, development_data=development_data, settings=self.settings)
        return self

    def predict(self, sources: List[List[str]], features: Optional[List[List[str]]] = None) -> List[Prediction]:
        if self.model is None:
            raise RuntimeError("Running inference with uninitialised model")

        evaluation_dataset = SequenceLabellingDataset(
            dataset=RawDataset(sources=sources, targets=None, features=features),
            source_vocabulary=self.model.source_vocabulary, feature_vocabulary=self.model.feature_vocabulary
        )
        evaluation_dataloader = DataLoader(
            evaluation_dataset, batch_size=self.settings.batch_size, shuffle=False,
            collate_fn=evaluation_dataset.collate_fn
        )

        predictions = []
        model = self.model.model.to(self.settings.device).eval()

        for batch in tqdm(evaluation_dataloader, desc="Prediction Progress"):
            with torch.no_grad():
                logits = model(
                    inputs=batch.sources, lengths=batch.source_lengths,
                    features=batch.features, feature_lengths=batch.feature_lengths
                )
                batch_predictions = self.inference(
                    model=model, logits=logits, lengths=batch.source_lengths, tau=self.settings.tau,
                    sources=batch.raw_sources, target_vocabulary=self.model.target_vocabulary
                )
                predictions.extend(batch_predictions)

        return predictions
