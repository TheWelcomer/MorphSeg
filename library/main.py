from dataset import RawDataset
from settings import Settings
from sequence_labeller import SequenceLabeller
import pandas as pd
import torch


def train():
    train = pd.read_csv('data/processed_data/ces/train.csv').values.tolist()
    test = pd.read_csv('data/processed_data/ces/test.csv').values.tolist()
    sources_train = [x[0] for x in train]
    targets_train = [x[1] for x in train]
    sources_test = [x[0] for x in test]
    targets_test = [x[1] for x in test]
    train_data = RawDataset(sources=sources_train, targets=targets_train, features=None)
    test_data = RawDataset(sources=sources_test, targets=targets_test, features=None)
    settings = Settings(
            name="pos_test", save_path="saved_models/test", loss="crf",
            device=torch.device("mps"), report_progress_every=100, epochs=30, tau=1
        )
    labeller = SequenceLabeller(settings=settings)
    labeller = labeller.fit(train_data=train_data, development_data=test_data)
    predictions = labeller.predict(sources=source_test)
    print(predictions)


if __name__ == "__main__":
    train()
