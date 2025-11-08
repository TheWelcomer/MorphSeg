# Sequence-Labelling

This repository contains implementations of LSTM based sequence labelling models.
Currently implemented are:
  * Standard single label sequence labelling with cross-entropy loss
  * LSTM-CRF (Huang et al., 2015)
  * CTC based model (Libovický and Jindřich Helcl, 2018). This model can be used for sequence
    tasks where the target sequence has different length than the source sequence. The number of
    source symbols is increased by a given multiplicative constant $\tau$ to allow target
    sequences that are longer than the source sequence.
  * CTC-CRF: Like CRF but allows to predict blanks. Note that this implementation does
    not truncate repeated symbols. If target sequences can be longer than source sequences,
    please make use of the $\tau$ parameter (see above).

## Usage
Using this code requires 3 steps.

### 1. Load your data
This repository does not provide any specific data loading routines.
Once you have loaded your data, you need to store it as a `RawDataset` object.
Assuming you have stored the source sequences (lists of strings) as `sources` and your target
sequences (also lists of strings) as `targets`, the following code gives an example:

```python
from dataset import RawDataset

train_data = RawDataset(sources=sources_train, targets=targets_train, features=None)
dev_data = RawDataset(sources=sources_dev, targets=targets_dev, features=None)
```

`RawDataset` is a `namedtuple`, so there are no default values which means you have to
explicitly state `features=None`. For tasks where there are additional sequence level features
encoded by a sequence of strings, you can pass them there.
In this case, also don't forget set `use_features=True` in the settings (see below).
Features are processed by BiLSTM and combined into a single vector by attention or pooling.
You can set some hyperparameters of feature encoding (see the `Settings` class).

### 2. Define settings
In file `settings.py`, we define a `Settings` object that holds all hyperparameter values.
For your experiment, you have to create an instance by passing your hyperparameters.
There are 2 required hyperparameters, namely `name`, which sets the name of the experiment,
and `save_path`, which defines where model checkpoints are saved.

```python
import torch
from settings import Settings

settings = Settings(
        name="pos_test", save_path="saved_models/test", loss="crf",
        device=torch.device("cuda:0"), report_progress_every=100, epochs=30, tau=1
    )
```

The most important hyperparameter is `loss`, which defines which type of sequence labelling
model you want to use. Currently, the available options are `cross-entropy`, `crf`, 
`ctc`, and `ctc-crf`. When using CTC or CTC-CRF, please also set `tau`.
You should not set `tau` when not using CTC or CTC-CRF.

### 3. Train models and make predictions
This repository provides a single model that takes a `Settings` object as parameter.
Then, call the `fit` method to train the model.
To make predictions, you can use the `predict` method.
The `predict` method takes lists of strings as input and outputs a list of `Prediction`
object. Each `Prediction` object contains the complete predicted sequence and the
alignment of predicted symbols to source symbols.

You can also load models by using `SequenceLabeller.load`.

```python
from sequence_labeller import SequenceLabeller

labeller = SequenceLabeller(settings=settings)
labeller = labeller.fit(train_data=train_data, development_data=dev_data)

predictions = labeller.predict(sources=source_test)
```

## References
 * Huang, Zhiheng, Wei Xu, and Kai Yu.
   "[Bidirectional LSTM-CRF models for sequence tagging](https://arxiv.org/abs/1508.01991)"
   arXiv preprint arXiv:1508.01991 (2015).
 * Jindřich Libovický and Jindřich Helcl. 2018. [End-to-End Non-Autoregressive Neural Machine Translation
   with Connectionist Temporal Classification.](https://aclanthology.org/D18-1336/)
   In Proceedings of the 2018 Conference on Empirical Methods in 
   Natural Language Processing, pages 3016–3021, Brussels, Belgium. Association for Computational Linguistics.
