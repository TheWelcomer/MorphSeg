import torch
import re
from sequence_labeller import SequenceLabeller
from oracle import sent2rules_strict, rules2sent_strict
from settings import Settings
from dataset import RawDataset
import os
import pandas as pd
import ast

class MorphemeSegmenter:
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
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cpu')
        self.sequence_labeller = SequenceLabeller.load(f"pretrained_models/{lang}.pt", self.device)
        self.sequence_labeller.settings.device = self.device
        self.sequence_labeller.model.model.to(self.device)
        self.sequence_labeller.model.model.device = self.device
        self.settings = self.sequence_labeller.settings

    def segment(self, text, output_string=False, delimiter=" @@"):
        if self.sequence_labeller is None:
            raise RuntimeError("Model not trained. Please train the model before segmentation.")
        if type(text) is not str:
            raise ValueError("Input sequence must be a string.")
        if type(output_string) is not bool:
            raise ValueError("output_string must be a boolean.")
        if type(delimiter) is not str:
            raise ValueError("Delimiter must be a string.")
        if text == "":
            return []

        # Extract all words
        words = re.findall(r"[a-zA-Z'-]+", text)
        words = [list(word.lower()) for word in words]
        # Process all words at once
        predictions = self.sequence_labeller.predict(sources=words)
        actions = [pred.prediction for pred in predictions]
        predicted_segmentations = [rules2sent_strict(source=words[i], actions=actions[i]).replace(" @@", delimiter) for i in range(len(words))]
        if output_string is True:
            # Create iterator for transformed words
            word_iter = iter(predicted_segmentations)
            # Replace each match with next transformed word
            return re.sub(r"[a-zA-Z'-]+", lambda m: next(word_iter), text)
        if output_string is False:
            if delimiter == "":
                return [[char for char in seg] for seg in predicted_segmentations]
            return [word.split(delimiter) for word in predicted_segmentations]

    def train(self, data_filepath: str, save_path: str, **kwargs):
        if self.train_from_scratch is True:
            self._train_from_scratch(data_filepath, save_path, **kwargs)
        # if self.train_from_scratch is False:
        #     self._fine_tune(data_filepath, save_path, **kwargs)

    def _load_data(self, data_filepath: str) -> RawDataset:
        if data_filepath.endswith('.csv'):
            df = pd.read_csv(data_filepath)
        elif data_filepath.endswith('.tsv'):
            df = pd.read_csv(data_filepath, sep='\t')
        else:
            raise ValueError("Data file must be a .csv or .tsv file.")

        sources = []
        targets = []
        label_set = set()

        non_string_skip = 0
        empty_source_skip = 0
        failed = 0
        passed = 0

        # Process each row
        for _, row in df.iterrows():
            source_word = row[df.columns[0]]
            target_word = row[df.columns[1]]

            # Skip non-string entries
            if not isinstance(source_word, str) or not isinstance(target_word, str):
                non_string_skip += 1
                continue

            # Skip empty source entries
            if len(source_word) == 0:
                empty_source_skip += 1
                continue

            try:
                # Use oracle to convert to input chars and action sequence
                input_chars, actions = sent2rules_strict(source_word, target_word)

                # Verify reconstruction
                reconstructed = rules2sent_strict(source_word, actions)

                # Verify invariants
                assert len(input_chars) == len(source_word), "Input length mismatch"
                assert len(actions) == len(source_word), "Action length mismatch"
                assert reconstructed == target_word, f"Reconstruction failed: got '{reconstructed}', expected '{target_word}'"

                sources.append(input_chars)
                targets.append(actions)

                # Track unique labels
                for action in actions:
                    label_set.add(action)

                passed += 1

            except Exception as e:
                print(f"Warning: Failed to process '{source_word}' -> '{target_word}': {e}")
                failed += 1
                continue

        # Print summary statistics
        print("=" * 80)
        print(f"DATA LOADING RESULTS: {data_filepath}")
        print("=" * 80)
        print(f"Total entries: {len(df)}")
        print(f"Successfully processed: {passed}")
        print(f"Failed: {failed}")
        print(f"Non-string entries (skipped): {non_string_skip}")
        print(f"Empty source entries (skipped): {empty_source_skip}")
        print(f"Total unique action labels: {len(label_set)}")
        print(
            f"Success rate: {passed}/{passed + failed} ({100 * passed / (passed + failed) if passed + failed > 0 else 0:.1f}%)")
        print("=" * 80)

        return RawDataset(sources=sources, targets=targets, features=None)

    def _train_from_scratch(self, train_data_filepath: str, save_path: str, test_data_filepath: str = None, **kwargs) -> None:
        if not os.path.exists(train_data_filepath):
            raise FileNotFoundError(f"Training data file '{train_data_filepath}' not found.")
        if test_data_filepath is not None and not os.path.exists(test_data_filepath):
            raise FileNotFoundError(f"Test data file '{test_data_filepath}' not found.")

        # Load train and test data
        train_data = self._load_data(train_data_filepath)
        test_data = self._load_data(test_data_filepath) if test_data_filepath is not None else None

        # Initialize settings
        settings = Settings(name=self.lang, save_path=save_path, **kwargs)

        # Create and train model
        self.labeller = SequenceLabeller(settings=settings)
        self.labeller.fit(train_data=train_data, development_data=test_data)

    def eval_model(self, test_data_filepath: str) -> dict:
        test_data = self._load_data(test_data_filepath)
        sources_test = test_data.sources
        targets_test = test_data.targets
        predictions = self.labeller.predict(sources=sources_test)

        # Word-level accuracy
        num_correct = 0

        # Edit distance
        total_edit_distance = 0

        # Boundary-level metrics
        true_positives = 0  # Correctly predicted boundaries
        false_positives = 0  # Incorrectly predicted boundaries
        false_negatives = 0  # Missed boundaries

        for i in range(len(predictions)):
            ground_truth = targets_test[i]
            prediction = predictions[i]
            target_seq = prediction.prediction
            source_seq = [prediction.alignment[j].symbol for j in range(len(prediction.alignment))]

            # Reconstruct segmentations
            predicted_segmentation = rules2sent_strict(source_seq, target_seq)
            gold_segmentation = rules2sent_strict(source_seq, ground_truth)

            # Word-level accuracy (exact match)
            if target_seq == ground_truth:
                num_correct += 1

            # Calculate edit distance (Levenshtein distance)
            edit_dist = self._levenshtein_distance(predicted_segmentation, gold_segmentation)
            total_edit_distance += edit_dist

            # Calculate boundary-level metrics
            # Extract boundary positions from segmentations
            pred_boundaries = self._extract_boundaries(predicted_segmentation)
            gold_boundaries = self._extract_boundaries(gold_segmentation)

            # Count true positives, false positives, and false negatives
            for boundary in pred_boundaries:
                if boundary in gold_boundaries:
                    true_positives += 1
                else:
                    false_positives += 1

            for boundary in gold_boundaries:
                if boundary not in pred_boundaries:
                    false_negatives += 1

        # Calculate metrics
        word_accuracy = num_correct / len(predictions) if len(predictions) > 0 else 0
        avg_edit_distance = total_edit_distance / len(predictions) if len(predictions) > 0 else 0

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Print summary
        print("=" * 80)
        print("EVALUATION RESULTS")
        print("=" * 80)
        print(f"Total words evaluated:     {len(predictions)}")
        print(f"\nWord-Level Metrics:")
        print(f"  Exact match accuracy:    {num_correct}/{len(predictions)} = {word_accuracy:.2%}")
        print(f"\nSegmentation Quality:")
        print(f"  Average edit distance:   {avg_edit_distance:.2f}")
        print(f"\nBoundary-Level Metrics:")
        print(f"  Precision:               {precision:.4f} ({precision * 100:.2f}%)")
        print(f"  Recall:                  {recall:.4f} ({recall * 100:.2f}%)")
        print(f"  F1 Score:                {f1:.4f} ({f1 * 100:.2f}%)")
        print(f"\nBoundary Counts:")
        print(f"  True Positives:          {true_positives}")
        print(f"  False Positives:         {false_positives}")
        print(f"  False Negatives:         {false_negatives}")
        print("=" * 80)

        return {
            'word_accuracy': word_accuracy,
            'edit_distance': avg_edit_distance,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'num_words': len(predictions),
            'num_correct': num_correct,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _extract_boundaries(self, segmentation: str, delimiter: str = " @@") -> set:
        boundaries = set()
        pos = 0
        segments = segmentation.split(delimiter)
        for i, segment in enumerate(segments[:-1]):
            pos += len(segment)
            boundaries.add(pos)
        return boundaries
    #
    # def _fine_tune(
    #     self, data_filepath: str, save_path: str, name=self.lang, epochs: int = self.settings.epochs,
    #     batch_size: int = self.settings.batch_size, device: torch.device = self.settings.device,
    #     scheduler: str = self.settings.scheduler, gamma: float = self.settings.gamma,
    #     verbose: bool = self.settings.verbose, report_progress_every: int = self.settings.report_progress_every,
    #     main_metric: str = self.settings.main_metric,
    #     keep_only_best_checkpoint: bool = self.settings.keep_only_best_checkpoint,
    #     optimizer: str = self.settings.optimizer, lr: float = self.settings.lr,
    #     weight_decay: float = self.settings.weight_decay, grad_clip: Optional[float] = self.settings.grad_clip,
    #     hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0, tau: int = 1, loss: str = "cross-entropy"
    # ) -> None:
    #     return
