# testmorphseg/training/trainer.py

import os
import torch
import numpy as np
import torch.nn as nn
import json
from safetensors.torch import save_file, load_file

from typing import List
from typing import Tuple
from testmorphseg.utils.logger import logger
from typing import Callable
from typing import Optional
from testmorphseg.models.model import LSTMModel
from testmorphseg.training.metrics import Metrics
from testmorphseg.utils.settings import Settings
from testmorphseg.training.dataset import RawDataset
from testmorphseg.training.metrics import get_metrics
from testmorphseg.training.metrics import metric_names
from collections import namedtuple
from torch.utils.data import DataLoader
from torch.nn.utils import clip_grad_value_
from testmorphseg.training.dataset import SequenceLabellingDataset
from testmorphseg.training.vocabulary import SequenceLabellingVocabulary
from torch.optim import SGD, Adam, AdamW, Optimizer
from testmorphseg.training.inference import argmax_decode, viterbi_decode, ctc_crf_decode
from testmorphseg.training.loss import ctc_loss, crf_loss, cross_entropy_loss, ctc_crf_loss
from torch.optim.lr_scheduler import ExponentialLR, OneCycleLR

Sequence = List[str]
Sequences = List[Sequence]
TrainData = Tuple[Sequences, Sequences]

DatasetCollection = namedtuple(
    "DatasetCollection",
    field_names=["source_vocabulary", "target_vocabulary", "feature_vocabulary", "train_dataset", "development_dataset"]
)
TrainedModel = namedtuple(
    "TrainedModel",
    ["model", "source_vocabulary", "target_vocabulary", "feature_vocabulary", "metrics", "checkpoint", "settings"]
)


def _prepare_datasets(train_data: RawDataset, development_data: Optional[RawDataset] = None,
                      use_features: bool = False) -> DatasetCollection:
    assert train_data.targets is not None
    source_vocabulary = SequenceLabellingVocabulary.build_vocabulary(train_data.sources)
    target_vocabulary = SequenceLabellingVocabulary.build_vocabulary(train_data.targets)

    if use_features:
        assert train_data.features is not None
        feature_vocabulary = SequenceLabellingVocabulary.build_vocabulary(train_data.features)
    else:
        feature_vocabulary = None

    train_dataset = SequenceLabellingDataset(
        dataset=train_data, source_vocabulary=source_vocabulary, target_vocabulary=target_vocabulary,
        feature_vocabulary=feature_vocabulary
    )

    if development_data is not None:
        assert development_data.targets is not None
        if use_features:
            assert development_data.features is not None

        development_dataset = SequenceLabellingDataset(
            dataset=development_data, source_vocabulary=source_vocabulary, target_vocabulary=target_vocabulary,
            feature_vocabulary=feature_vocabulary
        )
    else:
        development_dataset = None

    return DatasetCollection(
        source_vocabulary=source_vocabulary,
        target_vocabulary=target_vocabulary,
        feature_vocabulary=feature_vocabulary,
        train_dataset=train_dataset,
        development_dataset=development_dataset
    )


def _build_model(source_vocab_size: int, target_vocab_size: int, settings: Settings) -> LSTMModel:
    use_crf = "crf" in settings.loss

    return LSTMModel(
        vocab_size=source_vocab_size, num_labels=target_vocab_size, embedding_size=settings.embedding_size,
        hidden_size=settings.hidden_size, num_layers=settings.num_layers, dropout=settings.dropout,
        tau=settings.tau, use_crf=use_crf, device=settings.device, use_features=settings.use_features,
        feature_embedding_size=settings.feature_embedding_size, feature_hidden_size=settings.feature_hidden_size,
        feature_num_layers=settings.feature_num_layers, feature_pooling=settings.feature_pooling
    )


def _build_optimizer(model: LSTMModel, optimizer: str, lr: float, weight_decay: float) -> Optimizer:
    optimizer_map = {"sgd": SGD, "adam": Adam, "adamw": AdamW}
    try:
        return optimizer_map[optimizer](model.parameters(), lr=lr, weight_decay=weight_decay)
    except KeyError:
        raise ValueError(f"Unknown optimizer: {optimizer}")


def _build_scheduler(optimizer: Optimizer, scheduler: str, gamma: float, lr: float,
                     total_steps: int) -> Callable[[bool], None]:
    if scheduler == "exponential":
        scheduler_instance = ExponentialLR(optimizer=optimizer, gamma=gamma)
    elif scheduler == "one-cycle":
        scheduler_instance = OneCycleLR(optimizer=optimizer, max_lr=lr, total_steps=total_steps)
    else:
        raise ValueError(f"Unknown scheduler: {scheduler}")

    def scheduler_step(epoch_end: bool):
        if scheduler == "exponential" and epoch_end:
            scheduler_instance.step()
        elif scheduler == "one-cycle" and not epoch_end:
            scheduler_instance.step()

    return scheduler_step


def _get_loss_function(loss: str) -> Tuple[Callable, Callable]:
    if loss == "cross-entropy":
        return cross_entropy_loss, argmax_decode
    elif loss == "ctc":
        return ctc_loss, argmax_decode
    elif loss == "crf":
        return crf_loss, viterbi_decode
    elif loss == "ctc-crf":
        return ctc_crf_loss, ctc_crf_decode
    else:
        raise ValueError(f"Unknown loss: {loss}")


def _count_model_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def moving_avg_loss(old_loss: float, new_loss: float, gamma: float = 0.95) -> float:
    if old_loss is None:
        return new_loss
    else:
        return gamma * old_loss + (1 - gamma) * new_loss


def save_model(model: TrainedModel, name: str, path: str) -> str:
    os.makedirs(path, exist_ok=True)
    model_save_path = os.path.join(path, f"{name}.safetensors")

    metadata = {
        "model_config": json.dumps(model.model.get_params()),
        "settings": json.dumps(model.settings.__dict__, default=str),
        "source_vocabulary": json.dumps(model.source_vocabulary.alphabet),
        "target_vocabulary": json.dumps(model.target_vocabulary.alphabet),
    }
    if model.feature_vocabulary:
        metadata["feature_vocabulary"] = json.dumps(model.feature_vocabulary.alphabet)

    save_file(model.model.state_dict(), model_save_path, metadata=metadata)
    return model_save_path


def load_model(path: str, device) -> TrainedModel:
    state_dict = load_file(path, device=device.type)

    with open(path, 'rb') as f:
        header_len_bytes = f.read(8)
        header_len = int.from_bytes(header_len_bytes, 'little')
        header_json_bytes = f.read(header_len)
        header = json.loads(header_json_bytes.decode('utf-8'))

    metadata = header.get('__metadata__', {})

    model_config = json.loads(metadata["model_config"])
    model_config['device'] = device
    model = LSTMModel(**model_config)
    model.load_state_dict(state_dict)
    model.to(device)

    settings_dict = json.loads(metadata["settings"])
    settings_dict['device'] = device
    settings = Settings(**{k: v for k, v in settings_dict.items() if k in Settings.__init__.__code__.co_varnames})

    def vocab_from_alphabet(alphabet_list):
        specials = [SequenceLabellingVocabulary.PAD_TOKEN, SequenceLabellingVocabulary.UNK_TOKEN]
        symbols = [token for token in alphabet_list if token not in specials]
        return SequenceLabellingVocabulary(symbols=symbols)

    source_vocabulary = vocab_from_alphabet(json.loads(metadata["source_vocabulary"]))
    target_vocabulary = vocab_from_alphabet(json.loads(metadata["target_vocabulary"]))

    feature_vocabulary = None
    if "feature_vocabulary" in metadata:
        feature_vocabulary = vocab_from_alphabet(json.loads(metadata["feature_vocabulary"]))

    return TrainedModel(
        model=model,
        source_vocabulary=source_vocabulary,
        target_vocabulary=target_vocabulary,
        feature_vocabulary=feature_vocabulary,
        metrics=None,
        checkpoint=None,
        settings=settings
    )


def evaluate_on_development_data(model: TrainedModel, development_data: SequenceLabellingDataset,
                                 batch_size: int, loss: str) -> Metrics:
    get_loss, inference = _get_loss_function(loss=loss)
    target_vocabulary = model.target_vocabulary

    development_dataloader = DataLoader(
        development_data, batch_size=batch_size, shuffle=False, collate_fn=development_data.collate_fn
    )

    losses, predictions, targets = [], [], []

    with torch.no_grad():
        for batch in development_dataloader:
            batch_model_output = get_loss(model=model.model.eval(), batch=batch, reduction="none")
            losses.extend(batch_model_output.loss.detach().cpu().flatten().tolist())

            batch_predictions = inference(
                model=model.model.eval(), logits=batch_model_output.logits, lengths=batch.source_lengths,
                target_vocabulary=target_vocabulary, tau=model.model.tau, sources=batch.raw_sources
            )
            predictions.extend([p.prediction for p in batch_predictions])
            targets.extend(batch.raw_targets)

    return get_metrics(predictions=predictions, targets=targets, losses=losses)


def train(train_data: RawDataset, development_data: Optional[RawDataset], settings: Settings) -> TrainedModel:
    if settings.verbose:
        logger.info("Prepare for Training")
    dataset_collection = _prepare_datasets(
        train_data=train_data, development_data=development_data, use_features=settings.use_features
    )
    train_dataset, dev_dataset = dataset_collection.train_dataset, dataset_collection.development_dataset
    source_vocabulary, target_vocabulary, feature_vocabulary = (
        dataset_collection.source_vocabulary, dataset_collection.target_vocabulary,
        dataset_collection.feature_vocabulary
    )

    train_dataloader = DataLoader(
        train_dataset, batch_size=settings.batch_size, shuffle=True, collate_fn=train_dataset.collate_fn
    )
    total_steps = settings.epochs * len(train_dataloader)

    model = _build_model(
        source_vocab_size=len(source_vocabulary), target_vocab_size=len(target_vocabulary), settings=settings
    )
    model.to(device=settings.device).train()

    optimizer = _build_optimizer(
        model=model, optimizer=settings.optimizer, lr=settings.lr, weight_decay=settings.weight_decay
    )
    scheduler_step = _build_scheduler(
        optimizer, scheduler=settings.scheduler, gamma=settings.gamma, lr=settings.lr, total_steps=total_steps
    )
    get_loss, _ = _get_loss_function(loss=settings.loss)

    if settings.verbose:
        logger.info("Start Training")

    running_loss, step_counter, best_model_metric = None, 0, np.inf
    best_checkpoint_path = None

    for epoch in range(1, settings.epochs + 1):
        model.train()
        epoch_losses = []
        for batch in train_dataloader:
            optimizer.zero_grad()
            loss = get_loss(model=model, batch=batch, reduction="mean").loss
            loss.backward()
            if settings.grad_clip:
                clip_grad_value_(model.parameters(), settings.grad_clip)
            optimizer.step()
            scheduler_step(False)

            step_counter += 1
            loss_item = loss.detach().cpu().item()
            running_loss = moving_avg_loss(running_loss, loss_item)
            epoch_losses.append(loss_item)

            if settings.verbose and (step_counter % settings.report_progress_every == 0 or step_counter == 1):
                progress = 100 * step_counter / total_steps
                lr = optimizer.param_groups[0]['lr']
                logger.info(
                    f"[{progress:.2f}%] Loss: {running_loss:.3f} || LR: {lr:.6f} || Step {step_counter}/{total_steps}")

        epoch_model = TrainedModel(model, source_vocabulary, target_vocabulary, feature_vocabulary, None, None,
                                   settings)
        development_metrics = None
        if dev_dataset:
            development_metrics = evaluate_on_development_data(epoch_model, dev_dataset, settings.batch_size,
                                                               settings.loss)
            if settings.verbose:
                logger.info(f"[Dev metrics] Loss: {development_metrics.loss:.4f} || WER: {development_metrics.wer:.2f}")

        scheduler_step(True)
        epoch_model_metric = development_metrics[
            metric_names.index(settings.main_metric)] if development_metrics else np.mean(epoch_losses)
        model_improved = epoch_model_metric < best_model_metric

        if model_improved:
            best_model_metric = epoch_model_metric
            if settings.verbose:
                logger.info(f"Saving best model after epoch {epoch}")
            checkpoint_path = save_model(epoch_model, settings.name, settings.save_path)
            best_checkpoint_path = checkpoint_path

    if not best_checkpoint_path:
        best_checkpoint_path = save_model(epoch_model, settings.name, settings.save_path)

    return load_model(best_checkpoint_path, settings.device)