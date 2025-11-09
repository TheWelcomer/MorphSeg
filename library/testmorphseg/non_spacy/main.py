from .dataset import RawDataset
from .settings import Settings
from .sequence_labeller import SequenceLabeller
import pandas as pd
import torch
import ast
from .oracle import rules2sent_strict, run_oracle
import os
import re
from .morpheme_segmenter import MorphemeSegmenter
from importlib import resources
import pathlib

os.putenv("KMP_DUPLICATE_LIB_OK", "TRUE")

lang = "eng"
segmenter = MorphemeSegmenter(lang, train_from_scratch=True)
with resources.path(f"testmorphseg.non_spacy.data.raw_data.{lang}", f"train.tsv") as train_path:
    segmenter.train(
train_path,
        pathlib.Path(resources.files("testmorphseg.non_spacy.pretrained_models")),
        loss="crf",
        device=torch.device("cuda"),
        report_progress_every=1000,
        epochs=5,
        batch_size=256,
        lr=1e-3,
        embedding_size=32,
        hidden_size=64,
        tau=1)
with resources.path("testmorphseg.non_spacy.pretrained_models","eng.pt") as model_path:
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    print(checkpoint.get("model_class", None))
with resources.path(f"testmorphseg.non_spacy.data.raw_data.{lang}", f"test.tsv") as test_path:
    segmenter.eval_model(test_data_filepath=test_path)
    # input_text = "The unbelievably disagreeable preprocessor unsuccessfully reprocessed the unquestionably irreversible decontextualization"
    # segmented_text = segmenter.segment(input_text, output_string=True, delimiter=" @@")
    # print("Original Text: ", input_text)
    # print("Segmented Text: ", segmented_text)
