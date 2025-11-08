import torch
import re
from .sequence_labeller import SequenceLabeller
from .oracle import rules2sent_strict
from importlib import resources

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
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cpu')
        with resources.path("testmorphseg.non_spacy.pretrained_models", f"{lang}.pt") as model_path:#path relative to package
            self.sequence_labeller = SequenceLabeller.load(model_path, self.device)
        self.sequence_labeller.settings.device = self.device
        self.sequence_labeller.model.model.to(self.device)
        self.sequence_labeller.model.model.device = self.device

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
