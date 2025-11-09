from dataset import RawDataset
from settings import Settings
from sequence_labeller import SequenceLabeller
import pandas as pd
import torch
import ast
from oracle import rules2sent_strict, run_oracle
import os
import re
from morpheme_segmenter import MorphemeSegmenter

os.putenv("KMP_DUPLICATE_LIB_OK", "TRUE")

if __name__ == "__main__":
    segmenter = MorphemeSegmenter("ces", train_from_scratch=True)
    segmenter.train(
        "data/raw_data/ces/train.tsv",
        f"pretrained_models/",
        loss="crf",
        device=torch.device("mps"),
        report_progress_every=100,
        epochs=1,
        batch_size=32,
        lr=1e-3,
        embedding_size=64,
        hidden_size=128,
        tau=1)
    segmenter.eval_model(test_data_filepath="data/raw_data/ces/test.tsv")
    # input_text = "The unbelievably disagreeable preprocessor unsuccessfully reprocessed the unquestionably irreversible decontextualization"
    # segmented_text = segmenter.segment(input_text, output_string=True, delimiter=" @@")
    # print("Original Text: ", input_text)
    # print("Segmented Text: ", segmented_text)
