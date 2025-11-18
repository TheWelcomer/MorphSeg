import torch
import re
import os
import sys
import collections
import warnings
import pandas as pd
from icu import BreakIterator, Locale
import unicodedata2

from importlib import resources
from tqdm import tqdm
from huggingface_hub import HfApi, hf_hub_download, upload_file
from testmorphseg.interface.sequence_labeller import SequenceLabeller
from testmorphseg.training.oracle import sent2rules, rules2sent
from testmorphseg.utils.settings import Settings
from testmorphseg.training.dataset import RawDataset


class MorphemeSegmenter:
    PRETRAINED_REPO_PREFIX = 'MorphSeg'
    PRETRAINED_MODEL_LANGS = ['en', 'cs']

    def __init__(self, lang, load_pretrained=True, model_path=None, is_local=True):
        self.lang = lang
        self.load_pretrained = load_pretrained

        if torch.cuda.is_available():
            self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cpu')

        if type(lang) is not str:
            raise ValueError("Language must be a string.")
        if type(load_pretrained) is not bool:
            raise ValueError("load_pretrained must be a boolean.")

        if lang not in self.PRETRAINED_MODEL_LANGS and load_pretrained is True and model_path is None:
            warnings.warn(f"'{lang}' does not have a pretrained model and you've provided no saved model path. "
                          f"You must train from scratch using the train method.")
            self.load_pretrained = False
        if self.load_pretrained is False:
            print(f"Training model from scratch for language '{lang}'.")
            self.sequence_labeller = None
            return

        if model_path is not None:
            if is_local is False:
                print(f"Attempting to download model from Hub: {model_path} for language '{lang}'.")
                repo_id, filename = model_path.split('/')
                model_path = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=None)
            if is_local is True:
                print(f"Attempting to load local model for language '{lang}'.")
                self.sequence_labeller = SequenceLabeller.load(model_path, self.device)

        if model_path is None:
            repo_id = f"{self.PRETRAINED_REPO_PREFIX}/{lang}"
            filename = f"{lang}.safetensors"
            print(f"Attempting to load pretrained model from Hub: {repo_id}/{filename} for language '{lang}'.")
            model_file = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=None)
            self.sequence_labeller = SequenceLabeller.load(model_file, self.device)

        self.sequence_labeller.settings.device = self.device
        self.sequence_labeller.model.model.to(self.device)
        self.sequence_labeller.model.model.device = self.device
        print(f"Model for language '{lang}' loaded successfully.")

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

        bi = BreakIterator.createWordInstance(Locale(self.lang))
        bi.setText(text)

        tokens = []
        word_tokens = []
        word_positions = []

        start = 0
        end = bi.nextBoundary()

        while end != -1:
            token = text[start:end]
            rule_status = bi.getRuleStatus()
            is_word = rule_status >= 100

            tokens.append(token)

            if is_word:
                normalized_token = self._normalize_for_morphology(token)
                word_tokens.append(list(normalized_token))
                word_positions.append(len(tokens) - 1)

            start = end
            end = bi.nextBoundary()

        if not word_tokens:
            return [] if not output_string else text

        predictions = self.sequence_labeller.predict(sources=word_tokens)
        actions = [pred.prediction for pred in predictions]
        segmented = [
            rules2sent(source=word_tokens[i], actions=actions[i]).replace(" @@", delimiter)
            for i in range(len(word_tokens))
        ]

        if not output_string:
            if delimiter == "":
                return [[c for c in seg] for seg in segmented]
            return [seg.split(delimiter) for seg in segmented]

        seg_iter = iter(segmented)
        for pos in word_positions:
            tokens[pos] = next(seg_iter)

        return "".join(tokens)

    def _normalize_for_morphology(self, text: str) -> str:
        text = unicodedata2.normalize('NFKC', text)
        text = text.casefold()
        text = unicodedata2.normalize('NFC', text)
        return text

    def train(self, train_data_filepath: str, save_path: str, val_data_filepath=None, delimiter: str = ' @@', **kwargs):
        if self.sequence_labeller is None:
            print(f"Training model from scratch for language '{self.lang}'.")
            self._train_from_scratch(train_data_filepath, save_path, val_data_filepath, delimiter, **kwargs)
        else:
            print(f"Fine-tuning existing model for language '{self.lang}'.")
            self._fine_tune(train_data_filepath, save_path, val_data_filepath, delimiter, **kwargs)

    def _train_from_scratch(self, train_data_filepath: str, save_path: str, val_data_filepath: str, delimiter: str, **kwargs) -> None:
        if not os.path.exists(train_data_filepath):
            raise FileNotFoundError(f"Training data file '{train_data_filepath}' not found.")
        if val_data_filepath is not None and not os.path.exists(val_data_filepath):
            raise FileNotFoundError(f"Test data file '{val_data_filepath}' not found.")

        # Load train and test data
        train_data = self._load_data(train_data_filepath, delimiter)
        val_data = self._load_data(val_data_filepath, delimiter) if val_data_filepath is not None else None

        # Initialize settings
        settings = Settings(name=self.lang, save_path=save_path, **kwargs)

        # Create and train model
        self.sequence_labeller = SequenceLabeller(settings=settings)
        self.sequence_labeller.fit(train_data=train_data, development_data=val_data)

    def _fine_tune(self, train_data_filepath: str, save_path: str, val_data_filepath: str, delimiter: str, **kwargs) -> None:
        if not os.path.exists(train_data_filepath):
            raise FileNotFoundError(f"Training dataset '{train_data_filepath}' not found.")
        if val_data_filepath is not None and not os.path.exists(val_data_filepath):
            raise FileNotFoundError(f"Validation dataset '{val_data_filepath}' not found.")

        # Load train and val data and filtering datapoints the model can't handle
        val_data = None
        source_vocabulary = self.sequence_labeller.model.source_vocabulary
        target_vocabulary = self.sequence_labeller.model.target_vocabulary
        train_data = self._load_data(train_data_filepath, delimiter)
        train_data = self.filter_unsupported_segmentations(train_data, source_vocabulary, target_vocabulary, dataset_name='train')
        if val_data_filepath is not None:
            val_data = self._load_data(val_data_filepath, delimiter)
            val_data = self.filter_unsupported_segmentations(val_data, source_vocabulary, target_vocabulary, dataset_name='validation')

        self.sequence_labeller.settings.save_path = save_path
        fixed_settings = ['embedding_size', 'hidden_size', 'num_layers', 'use_features', 'feature_embedding_size',
                          'feature_hidden_size', 'feature_num_layers', 'feature_pooling',]

        for key, value in kwargs.items():
            if key in fixed_settings:
                warnings.warn(f"Warning: '{key}' setting cannot be changed during fine-tuning and will be ignored.")
                continue
            if not hasattr(self.sequence_labeller.settings, key):
                warnings.warn(f"Warning: Unknown/unsupported setting '{key}' will be ignored.")
                continue
            setattr(self.sequence_labeller.settings, key, value)

        # Create and train model
        self.sequence_labeller.fit(train_data=train_data, development_data=val_data)

    @staticmethod
    def filter_unsupported_segmentations(dataset: RawDataset, source_vocabulary, target_vocabulary, dataset_name='unknown') -> RawDataset:
        filtered_sources = []
        filtered_targets = []

        for i in range(len(dataset.sources)):
            source = dataset.sources[i]
            target = dataset.targets[i]

            source_in_vocab = all(char in source_vocabulary.token2idx for char in source)
            target_in_vocab = all(action in target_vocabulary.token2idx for action in target)

            if source_in_vocab and target_in_vocab:
                filtered_sources.append(source)
                filtered_targets.append(target)

        num_filtered = len(dataset.sources) - len(filtered_sources)
        pct_filtered = (num_filtered / len(dataset.sources)) * 100 if len(dataset.sources) > 0 else 0
        if num_filtered > 0:
            print(f"Filtered out {num_filtered} ({pct_filtered}%) unsupported datapoints due to unknown tokens/actions from the {dataset_name} dataset.")

        return RawDataset(sources=filtered_sources, targets=filtered_targets, features=None)

    @staticmethod
    def _load_data(data_filepath: str, delimiter: str) -> RawDataset:
        if str(data_filepath).endswith('.csv'):
            df = pd.read_csv(data_filepath)
        elif str(data_filepath).endswith('.tsv'):
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
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating Action Labels..."):
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
                target_word = target_word.replace(delimiter, " @@")
                # Use oracle to convert to input chars and action sequence
                input_chars, actions = sent2rules(source_word, target_word)

                # Verify reconstruction
                reconstructed = rules2sent(source_word, actions)

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

    def eval_model(self, test_data_filepath: str, delimiter: str = ' @@') -> dict:
        """
        Evaluates the model on a test dataset using SIGMORPHON-compatible metrics.
        This function now calculates precision, recall, and F1 score based on the
        multiset of morpheme strings, which is the official method used in the
        SIGMORPHON 2022 Shared Task.
        """
        test_data = self._load_data(test_data_filepath, delimiter)
        sources_test = test_data.sources
        targets_test = test_data.targets
        predictions = self.sequence_labeller.predict(sources=sources_test)

        # Word-level accuracy (exact match on action labels)
        num_correct = 0

        # Edit distance on reconstructed strings
        total_edit_distance = 0

        total_true_positives = 0
        total_false_positives = 0
        total_false_negatives = 0

        for i in range(len(predictions)):
            ground_truth_actions = targets_test[i]
            prediction_object = predictions[i]
            predicted_actions = prediction_object.prediction
            source_chars = [align_pos.symbol for align_pos in prediction_object.alignment]

            # Reconstruct the segmented strings
            predicted_segmentation = rules2sent(source_chars, predicted_actions)
            gold_segmentation = rules2sent(source_chars, ground_truth_actions)

            # --- Word-level accuracy (no change here) ---
            if predicted_actions == ground_truth_actions:
                num_correct += 1

            # --- Edit distance (no change here) ---
            edit_dist = self._levenshtein_distance(predicted_segmentation, gold_segmentation)
            total_edit_distance += edit_dist

            # Split the segmented strings into lists of morphemes
            # The delimiter is hard-coded as " @@" to match the oracle's output
            pred_morphemes = predicted_segmentation.split(" @@")
            gold_morphemes = gold_segmentation.split(" @@")

            # Use collections.Counter to handle multisets of morphemes correctly
            pred_morpheme_counts = collections.Counter(pred_morphemes)
            gold_morpheme_counts = collections.Counter(gold_morphemes)

            # True Positives: The intersection of the two multisets
            intersection_counts = pred_morpheme_counts & gold_morpheme_counts
            word_tp = sum(intersection_counts.values())

            # False Positives: Morphemes in prediction but not in gold
            word_fp = len(pred_morphemes) - word_tp

            # False Negatives: Morphemes in gold but not in prediction
            word_fn = len(gold_morphemes) - word_tp

            # Add the counts for this word to the dataset-wide totals
            total_true_positives += word_tp
            total_false_positives += word_fp
            total_false_negatives += word_fn

        # --- Calculate final metrics ---
        word_accuracy = num_correct / len(predictions) if len(predictions) > 0 else 0
        avg_edit_distance = total_edit_distance / len(predictions) if len(predictions) > 0 else 0

        precision = total_true_positives / (total_true_positives + total_false_positives) if (total_true_positives + total_false_positives) > 0 else 0
        recall = total_true_positives / (total_true_positives + total_false_negatives) if (total_true_positives + total_false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Print summary
        print("=" * 80)
        print("EVALUATION RESULTS (SIGMORPHON-COMPATIBLE)")
        print("=" * 80)
        print(f"Total words evaluated:     {len(predictions)}")
        print(f"\nWord-Level Metrics:")
        print(f"  Exact match accuracy (actions): {num_correct}/{len(predictions)} = {word_accuracy:.2%}")
        print(f"\nSegmentation Quality:")
        print(f"  Average edit distance:   {avg_edit_distance:.2f}")
        print(f"\nMorpheme-Level Metrics (Official):")
        print(f"  Precision:               {precision:.4f} ({precision * 100:.2f}%)")
        print(f"  Recall:                  {recall:.4f} ({recall * 100:.2f}%)")
        print(f"  F1 Score:                {f1:.4f} ({f1 * 100:.2f}%)")
        print(f"\nMorpheme Counts:")
        print(f"  True Positives:          {total_true_positives}")
        print(f"  False Positives:         {total_false_positives}")
        print(f"  False Negatives:         {total_false_negatives}")
        print("=" * 80)

        return {
            'word_accuracy': word_accuracy,
            'edit_distance': avg_edit_distance,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'num_words': len(predictions),
            'num_correct': num_correct,
            'true_positives': total_true_positives,
            'false_positives': total_false_positives,
            'false_negatives': total_false_negatives
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
# 1220
