import torch
import re
from sequence_labeller import SequenceLabeller
from oracle import sent2rules_strict, rules2sent_strict
from settings import Settings
from dataset import RawDataset

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
        if self.train_from_scratch is False:
            self._fine_tune(data_filepath, save_path, **kwargs)

    def _load_data(self, data_filepath: str) -> RawDataset:
        df = pd.read_csv(train_data_filepath)
        df[df.columns[0]] = train_df[df.columns[0]].apply(ast.literal_eval)
        df[df.columns[1]] = train_df[df.columns[1]].apply(ast.literal_eval)
        sources = train_df[df.columns[0]].tolist()
        targets = train_df[df.columns[1]].tolist()
        return RawDataset(sources=sources, targets=targets, features=None)

    def _train_from_scratch(self, train_data_filepath: str, save_path: str, test_data_filepath: str = None, **kwargs) -> None:
        if not os.path.exists(train_data_filepath):
            raise FileNotFoundError(f"Training data file '{train_data_filepath}' not found.")
        if test_data_filepath is not None and not os.path.exists(test_data_filepath):
            raise FileNotFoundError(f"Test data file '{test_data_filepath}' not found.")

        # Load train and test data
        train_data = self.load_data(train_data_filepath)
        test_data = self.load_data(test_data_filepath) if test_data_filepath is not None else None

        # Initialize settings
        settings = Settings(name=self.lang, **kwargs)

        # Create and train model
        labeller = SequenceLabeller(settings=settings)
        labeller = labeller.fit(train_data=train_data, development_data=test_data)

        # Predict with model
        # num_correct = 0
        # predictions = labeller.predict(sources=sources_test)
        # for i in range(len(predictions)):
        #     ground_truth = targets_test[i]
        #     prediction = predictions[i]
        #     target_seq = prediction.prediction
        #     source_seq = [prediction.alignment[i].symbol for i in range(len(prediction.alignment))]
        #     reconstructed_prediction = rules2sent_strict(source_seq, target_seq)
        #     print("Source: ", "".join(source_seq))
        #     print("Predicted Target: ", "".join(reconstructed_prediction))
        #     print("Ground Truth: ", "".join([rules2sent_strict(source_seq, ground_truth)]))
        #     print(f"Target Seq: {target_seq}")
        #     print(f"Ground Truth: {ground_truth}")
        #     if target_seq == ground_truth:
        #         num_correct += 1
        # print(f"Accuracy: {num_correct}/{len(predictions)} = {num_correct / len(predictions):.2%}")

    def _fine_tune(
        self, data_filepath: str, save_path: str, name=self.lang, epochs: int = self.settings.epochs,
        batch_size: int = self.settings.batch_size, device: torch.device = self.settings.device,
        scheduler: str = self.settings.scheduler, gamma: float = self.settings.gamma,
        verbose: bool = self.settings.verbose, report_progress_every: int = self.settings.report_progress_every,
        main_metric: str = self.settings.main_metric,
        keep_only_best_checkpoint: bool = self.settings.keep_only_best_checkpoint,
        optimizer: str = self.settings.optimizer, lr: float = self.settings.lr,
        weight_decay: float = self.settings.weight_decay, grad_clip: Optional[float] = self.settings.grad_clip,
        hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0, tau: int = 1, loss: str = "cross-entropy"
    ) -> None:
        return
