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

class Segmenter:
    def __init__(self, lang, train_from_scratch=False):
        self.lang = lang
        self.train_from_scratch = train_from_scratch
        if type(lang) is not str:
            raise ValueError("Language must be a string.")
        if type(train_from_scratch) is not bool:
            raise ValueError("train_from_scratch must be a boolean.")
        pretrained_model_langs = ["eng"]
        if lang not in pretrained_model_langs and train_from_scratch is False:
            print(f"'{lang}' does not have a pretrained model. You must train from scratch using the train method.")
            self.train_from_scratch = True
        if lang in pretrained_model_langs and train_from_scratch is False:
            print(f"Loading pretrained model for language '{lang}'.")
        if train_from_scratch is True:
            print(f"Training model from scratch for language '{lang}'.")
        if self.train_from_scratch is True:
            self.sequence_labeller = None
            return
        self.sequence_labeller = SequenceLabeller.load(f"pretrained_models/{lang}.pt")

    def segment(self, input_sequence, output_string=False, delimiter=" @@"):
        if self.sequence_labeller is None:
            raise RuntimeError("Model not trained. Please train the model before segmentation.")
        if type(input_sequence) is not str:
            raise ValueError("Input sequence must be a string.")
        if type(output_string) is not bool:
            raise ValueError("output_string must be a boolean.")
        if type(delimiter) is not str:
            raise ValueError("Delimiter must be a string.")
        if input_sequence == "":
            return []

        # Extract all words
        words = re.findall(r"[a-zA-Z'-]+", text)
        words = [list(word.lower()) for word in words]
        # Process all words at once
        actions = self.sequence_labeller.predict(sources=words).prediction
        predicted_segmentations = [rules2sent_strict(source=words[i], actions=actions[i]).replace(" @@", delimiter) for i in range(len(words))]
        if output_string is True:
            # Create iterator for transformed words
            word_iter = iter(transformed_words)
            # Replace each match with next transformed word
            return re.sub(r"[a-zA-Z'-]+", lambda m: next(word_iter), text)
        if output_string is False:
            return [predicted_segmentations.split(delimiter) for word in predicted_segmentations]





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
        save_path=f"pretrained_models/",
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
