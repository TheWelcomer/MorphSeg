# MorphSeg

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Test PyPI](https://img.shields.io/badge/Test%20PyPI-0.0.1-orange.svg)](https://test.pypi.org/project/testmorphseg/)

## Table of Contents
- [Introduction](#introduction)
- [Authors and License](#authors-and-license)
- [Background](#background)
  - [Problem](#problem)
  - [Motivation](#motivation)
  - [Approach](#approach)
  - [Example](#example)
- [Features](#features)
- [Library Usage](#library-usage)
  - [Installation](#installation)
  - [Language Codes with Pretrained Models](#language-codes-with-pretrained-models)
  - [Method Headers](#method-headers)
- [Script Examples](#script-examples)
  - [Segmentation](#segmentation)
  - [Training from Scratch](#training-from-scratch)

## Introduction
Welcome to the MorphSeg repository! This is a developing easy-to-use library for the [Tü_Seg model of morpheme segmentation](https://aclanthology.org/2022.sigmorphon-1.13/). This repo also contains code for a frontend demo website and a backend server which serves the MorphSeg library. This library is built on top of a research repository released by [Leander Girrbach](https://www.eml-munich.de/people/leander-girrbach) for his submission to [The SIGMORPHON 2022 Shared Task on Morpheme Segmentation](https://aclanthology.org/2022.sigmorphon-1.11/). We thank Leander Girrbach for open-sourcing his code and allowing us to build upon it and we thank the [SIGMORPHON 2022 Shared Task](https://aclanthology.org/2022.sigmorphon-1.11/) organizers for curating the datasets and hosting the shared task.

## Authors and License
This repository is licensed under the MIT license, please see the [LICENSE.TXT](library/LICENSE.TXT) for more details. The library is being developed and maintained by [Nathan Wolf](https://www.linkedin.com/in/nathanw0lf/) and [Donald Winkelman](https://www.dwink.dev/). [Cynthia Kong](https://www.linkedin.com/in/cynthia-kong-9785b2260/), [Alexis Therrien](https://github.com/block36underscore), and [Taoran Ye](https://www.linkedin.com/in/taoran-ye-5a103b359/) additionally created the frontend demo website for the MorphSeg library.

# Background
## Problem
The Problem of Morpheme Segmentation is as Follows: Given a word, what are the morphemes of the word?

## Motivation
Morphemes are the smallest meaningful units of text. For example, segmenting the word "morphemes" would look something like ["morph","eme","s"]. There are 2 types of morpheme segmentation: surface and canonical. This library does canonical morpheme segmentation, as it is more linguistically meaningful, ignoring things like inflection and conjugation to display the true morphemes. For example, while a surface segmentation of "manliness" might be ["man","li","ness"], a canonical segmentation would be ["man","ly","ness"], allowing for the "li" morpheme of "manliness" to be counted as an occurence of "ly", as it should. This is useful for many different linguistic/NLP analyses of text, as you can more easily determine the meaningful features imparted on words by their morphemes.

## Approach
We solve this problem by making use of a BiLSTM-CRF model architecture named Tü_Seg, which has been shown to be effective for sequence labeling tasks such as morpheme segmentation. A major advantage of this model is its small size (~5-50 MB) and extremely fast speed even on a CPU. Tü_Seg outputs BIO tags for each character in the input word. Each BIO tag contains a list of actions to be performed on the character to map it to the segmented output. The actions are as follows:
- COPY: Copy the character to the output.
- SEP: Append a morpheme separator (e.g., " @@") to the output after the character.
- DELETE: Do not copy the character to the output.
- (ADD_<char>): Add the character <char> to the output.

## Example
Given the input word "unhappiness", the model might output the following BIO tags:
- u: [COPY
- n: [COPY]
- h: [COPY]
- a: [COPY]
- p: [COPY]
- p: [COPY]
- i: [ADD_y, SEP]
- n: [COPY]
- e: [COPY]
- s: [COPY]
- s: [COPY]

# Features
The MorphSeg library provides the following features:
- Easy-to-use API for morpheme segmentation.
  - You can input a string of any length and receive the segmented output as either a string or a list.
- Pretrained models for multiple languages.
- Ability to train custom models from scratch.
- Support for both CPU and GPU training and inference.

# Library Usage
All functionalities of the MorphSeg library are encapsulated in the `MorphemeSegmenter` class, you should initialize an instance of this class for each model you want to use. Currently, each model and its corresponding `MorphemeSegmenter` object is specific to one language, so you must specify the language when initializing the object. If the language code has a pretrained model available, it will be used unless you set `train_from_scratch=True` during initialization.

## Installation
The MorphSeg library is currently [deployed on Test PyPI](https://test.pypi.org/project/testmorphseg/), the package drafting version of PyPI. To install it, you can use pip. Run the following command in your terminal:
```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ testmorphseg
```
If you want to install using a `requirements.txt` (for venv) or `environment.yml` (for conda), you can add the following:
```bash
--extra-index-url https://test.pypi.org/simple
testmorphseg==0.0.1
```

## Language Codes with Pretrained Models:
- English: "eng"

## Method Headers:
```python
# Morpheme Segmenter Class Initialization
def __init__(self, lang, train_from_scratch=False):
    pass

# Segment Method
def segment(self, text, output_string=False, delimiter=" @@"):
    pass

# Train Method
def train(self, train_data_filepath: str, save_path: str, test_data_filepath: str = None, 
                 name: str = self.lang, epochs: int = 1, batch_size: int = 32,
                 device: torch.device = torch.device("cpu"), scheduler: str = "exponential", gamma: float = 1.0,
                 verbose: bool = True, report_progress_every: int = 1, main_metric: str = "wer",
                 keep_only_best_checkpoint: bool = True, optimizer: str = "adam", lr: float = 1e-3,
                 weight_decay: float = 0.0, grad_clip: Optional[float] = None, embedding_size: int = 64,
                 hidden_size: int = 128, num_layers: int = 1, dropout: float = 0.0, tau: int = 1,
                 loss: str = "cross-entropy", use_features: bool = False, feature_embedding_size: int = 32,
                 feature_hidden_size: int = 128, feature_num_layers: int = 0, feature_pooling: str = "mean") -> None:
    pass

# Eval Method
def eval_model(self, test_data_filepath: str) -> dict:
    pass
```

# Script Examples
## Segmentation
Here is a simple script that segments input text using the MorphSeg library:
```python
## TODO: After creating a virtual environment (venv or conda), run the following command to install testmorphseg from Test PyPI:
## pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ testmorphseg
from testmorphseg import MorphemeSegmenter

if __name__ == '__main__':
    segmenter = MorphemeSegmenter(lang="eng")
    input_text = ("The unbelievably disagreeable preprocessor unsuccessfully reprocessed "
                  "the unquestionably irreversible decontextualization")
    segmented_string = segmenter.segment(input_text, output_string=True)
    segmented_list = segmenter.segment(input_text)
    print("Original Text: ", input_text)
    print("Segmented Text: ", segmented_string)
    print("Segmented List: ", segmented_list)
```
## Training from Scratch
Here is a simple script that trains a model from scratch using the csv train_data.csv, saves the trained model to the pretrained_models/ directory, and evaluates it on test_data.csv:
```python
## TODO: After creating a virtual environment (venv or conda), run the following command to install testmorphseg from Test PyPI:
## pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ testmorphseg
from testmorphseg import MorphemeSegmenter

if __name__ == '__main__':
    segmenter = MorphemeSegmenter("eng", train_from_scratch=True)
    segmenter.train(
        "train_data.csv",
        "pretrained_models/",
        loss="crf",
        device=torch.device("cuda"),
        report_progress_every=1000,
        epochs=1,
        batch_size=256,
        lr=1e-3,
        embedding_size=32,
        hidden_size=64,
        tau=1)
    segmenter.eval_model("test_data.csv")
```