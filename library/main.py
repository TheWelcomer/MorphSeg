from dataset import RawDataset
from settings import Settings
from sequence_labeller import SequenceLabeller
import pandas as pd
import torch
from dotenv import load_dotenv
import ast
from oracle import rules2sent_strict, run_oracle
import os

os.putenv("KMP_DUPLICATE_LIB_OK", "TRUE")

def train(lang):
    if not os.path.exists(f'data/processed_data/{lang}/train.csv') or not os.path.exists(f'data/processed_data/{lang}/test.csv'):
        run_oracle(lang, "train")
        run_oracle(lang, "test")

    # Load CSVs
    train_df = pd.read_csv(f'data/processed_data/{lang}/train.csv')
    test_df = pd.read_csv(f'data/processed_data/{lang}/test.csv')

    # Convert stringified lists to Python lists
    train_df["source"] = train_df["source"].apply(ast.literal_eval)
    train_df["actions"] = train_df["actions"].apply(ast.literal_eval)
    test_df["source"] = test_df["source"].apply(ast.literal_eval)
    test_df["actions"] = test_df["actions"].apply(ast.literal_eval)

    # Extract lists
    sources_train = train_df["source"].tolist()
    targets_train = train_df["actions"].tolist()
    sources_test = test_df["source"].tolist()
    targets_test = test_df["actions"].tolist()

    # Build datasets
    train_data = RawDataset(sources=sources_train, targets=targets_train, features=None)
    test_data = RawDataset(sources=sources_test, targets=targets_test, features=None)

    # Initialize settings
    settings = Settings(
        name=f"{lang}",
        save_path=f"saved_models/",
        loss="crf",
        device=torch.device("cuda"),
        report_progress_every=1000,
        epochs=5,
        batch_size=256,
        lr=1e-3,
        embedding_size=64,
        hidden_size=128,
        tau=1,
    )

    # Create and train model
    labeller = SequenceLabeller(settings=settings)
    labeller = labeller.fit(train_data=train_data, development_data=test_data)

    # Predict with model
    num_correct = 0
    predictions = labeller.predict(sources=sources_test)
    for i in range(len(predictions)):
        ground_truth = targets_test[i]
        prediction = predictions[i]
        target_seq = prediction.prediction
        source_seq = [prediction.alignment[i].symbol for i in range(len(prediction.alignment))]
        reconstructed_prediction = rules2sent_strict(source_seq, target_seq)
        print("Source: ", "".join(source_seq))
        print("Predicted Target: ", "".join(reconstructed_prediction))
        print("Ground Truth: ", "".join([rules2sent_strict(source_seq, ground_truth)]))
        print(f"Target Seq: {target_seq}")
        print(f"Ground Truth: {ground_truth}")
        if target_seq == ground_truth:
            num_correct += 1
    print(f"Accuracy: {num_correct}/{len(predictions)} = {num_correct / len(predictions):.2%}")


if __name__ == "__main__":
    train("eng")
