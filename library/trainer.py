import os
import torch
import numpy as np
import torch.nn as nn

from typing import List
from typing import Tuple
from logger import logger
from typing import Callable
from typing import Optional
from model import LSTMModel
from metrics import Metrics
from settings import Settings
from dataset import RawDataset
from metrics import get_metrics
from metrics import metric_names
from collections import namedtuple
from torch.utils.data import DataLoader
from torch.nn.utils import clip_grad_value_
from dataset import SequenceLabellingDataset
from vocabulary import SequenceLabellingVocabulary
from torch.optim import SGD, Adam, AdamW, Optimizer
from inference import argmax_decode, viterbi_decode, ctc_crf_decode
from loss import ctc_loss, crf_loss, cross_entropy_loss, ctc_crf_loss
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

    # Define step function that calls step on epoch end for exponential scheduler,
    # and on update for one-cycle-scheduler
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
    model_save_info = dict()
    model_save_info["model_class"] = type(model.model)
    model_save_info["parameters"] = model.model.get_params()
    model_save_info["state_dict"] = model.model.state_dict()
    model_save_info["source_vocabulary"] = model.source_vocabulary
    model_save_info["target_vocabulary"] = model.target_vocabulary
    model_save_info["feature_vocabulary"] = model.feature_vocabulary
    model_save_info["metrics"] = model.metrics
    model_save_info["checkpoint"] = model.checkpoint
    model_save_info["settings"] = model.settings

    save_model_path = os.path.join(path, name + ".pt")
    torch.save(model_save_info, save_model_path)

    return save_model_path


def load_model(path: str) -> TrainedModel:
    model_save_info = torch.load(path)

    model = model_save_info["model_class"](**model_save_info["parameters"])
    model.load_state_dict(model_save_info["state_dict"])

    source_vocabulary = model_save_info["source_vocabulary"]
    target_vocabulary = model_save_info["target_vocabulary"]
    feature_vocabulary = model_save_info["feature_vocabulary"]
    metrics = model_save_info["metrics"]
    checkpoint = model_save_info["checkpoint"]
    settings = model_save_info["settings"]

    return TrainedModel(
        model=model, source_vocabulary=source_vocabulary, target_vocabulary=target_vocabulary,
        feature_vocabulary=feature_vocabulary, metrics=metrics, checkpoint=checkpoint, settings=settings
    )


def evaluate_on_development_data(model: TrainedModel, development_data: SequenceLabellingDataset,
                                 batch_size: int, loss: str) -> Metrics:
    get_loss, inference = _get_loss_function(loss=loss)
    target_vocabulary = model.target_vocabulary

    # Build dataloader
    development_dataloader = DataLoader(
        development_data, batch_size=batch_size, shuffle=False, collate_fn=development_data.collate_fn
    )

    losses = []
    predictions = []
    targets = []

    with torch.no_grad():
        for batch in development_dataloader:
            batch_model_output = get_loss(model=model.model.eval(), batch=batch, reduction="none")
            losses.extend(batch_model_output.loss.detach().cpu().flatten().tolist())

            batch_predictions = inference(
                model=model.model.eval(), logits=batch_model_output.logits, lengths=batch.source_lengths,
                target_vocabulary=target_vocabulary, tau=model.model.tau, sources=batch.raw_sources
            )
            batch_predictions = [prediction.prediction for prediction in batch_predictions]
            predictions.extend(batch_predictions)
            targets.extend(batch.raw_targets)

    metrics = get_metrics(predictions=predictions, targets=targets, losses=losses)
    return metrics


def train(train_data: RawDataset, development_data: Optional[RawDataset], settings: Settings) -> TrainedModel:
    if settings.verbose:
        logger.info("Prepare for Training")
        logger.info("Build vocabulary and datasets")

    # Build and unpack dataset info
    dataset_collection = _prepare_datasets(
        train_data=train_data, development_data=development_data, use_features=settings.use_features
    )
    train_dataset = dataset_collection.train_dataset
    dev_dataset = dataset_collection.development_dataset
    source_vocabulary = dataset_collection.source_vocabulary
    target_vocabulary = dataset_collection.target_vocabulary
    feature_vocabulary = dataset_collection.feature_vocabulary

    if settings.verbose:
        logger.info(f"Train data contains {len(train_dataset)} datapoints")
        if dev_dataset is not None:
            logger.info(f"Dev data contains {len(dev_dataset)} datapoints")
        logger.info(f"Source vocabulary contains {len(source_vocabulary)} items")
        logger.info(f"Target vocabulary contains {len(target_vocabulary)} actions")

    # Build training dataloader
    train_dataloader = DataLoader(
        train_dataset, batch_size=settings.batch_size, shuffle=True, collate_fn=train_dataset.collate_fn
    )
    total_steps = settings.epochs * len(train_dataloader)

    # Build model
    if settings.verbose:
        logger.info("Build model")

    model = _build_model(
        source_vocab_size=len(source_vocabulary), target_vocab_size=len(target_vocabulary), settings=settings
    )
    print(model)

    if settings.verbose:
        num_model_parameters = _count_model_parameters(model)
        logger.info(f"Model has {num_model_parameters} parameters")
        logger.info(f"Device: {settings.device}")
    model = model.to(device=settings.device)
    model = model.train()

    # Build optimizer
    if settings.verbose:
        logger.info("Build optimizer")
    optimizer = _build_optimizer(
        model=model, optimizer=settings.optimizer, lr=settings.lr, weight_decay=settings.weight_decay
    )

    # Build scheduler
    if settings.verbose:
        logger.info("Build scheduler")

    scheduler_step = _build_scheduler(
        optimizer, scheduler=settings.scheduler, gamma=settings.gamma, lr=settings.lr, total_steps=total_steps
    )

    # Get loss function
    get_loss, _ = _get_loss_function(loss=settings.loss)

    if settings.verbose:
        logger.info("Start Training")

    running_loss = None
    step_counter = 0
    best_model_metric = np.inf
    best_checkpoint_path = None

    for epoch in range(1, settings.epochs + 1):
        # Train epoch
        model = model.train()
        epoch_losses = []

        for batch in train_dataloader:
            optimizer.zero_grad()

            loss = get_loss(model=model, batch=batch, reduction="mean").loss

            # Update parameters
            loss.backward()
            if settings.grad_clip is not None:
                clip_grad_value_(model.parameters(), settings.grad_clip)
            optimizer.step()
            scheduler_step(False)

            # Display loss
            step_counter += 1
            loss_item = loss.detach().cpu().item()
            running_loss = moving_avg_loss(running_loss, loss_item)
            epoch_losses.append(loss_item)

            if settings.verbose:
                if step_counter % settings.report_progress_every == 0 or step_counter == 1:
                    progress = 100 * step_counter / total_steps
                    current_learning_rate = optimizer.param_groups[0]['lr']
                    logger.info(
                        f"[{progress:.2f}%]" +
                        f" Loss: {running_loss:.3f}" +
                        f" || LR: {current_learning_rate:.6f}" +
                        f" || Step {step_counter} / {total_steps}"
                    )

        # Evaluate on dev set
        epoch_model = TrainedModel(
            model=model, source_vocabulary=source_vocabulary, target_vocabulary=target_vocabulary,
            feature_vocabulary=feature_vocabulary, metrics=None, checkpoint=None, settings=settings
        )

        if dev_dataset is not None:
            development_metrics = evaluate_on_development_data(
                model=epoch_model, development_data=dev_dataset, batch_size=settings.batch_size, loss=settings.loss
            )

            if settings.verbose:
                logger.info(
                    f"[Development metrics]    " +
                    f"Loss: {development_metrics.loss:.4f}" +
                    f" || WER: {development_metrics.wer:.2f}" +
                    f" || Edit-Distance: {development_metrics.edit_distance:.2f}"
                )

        else:
            development_metrics = None

        scheduler_step(True)

        if development_metrics is not None:
            epoch_model_metric = development_metrics[metric_names.index(settings.main_metric)]
        else:
            epoch_model_metric = np.mean(epoch_losses)

        model_improved = epoch_model_metric < best_model_metric
        best_model_metric = epoch_model_metric if model_improved else best_model_metric

        if development_metrics is not None:
            save_metrics = development_metrics
        else:
            save_metrics = Metrics(
                loss=np.mean(epoch_losses), wer=None, ter=None, edit_distance=None, normalised_edit_distance=None
            )

        epoch_model = TrainedModel(
            model=model, source_vocabulary=source_vocabulary, target_vocabulary=target_vocabulary,
            feature_vocabulary=feature_vocabulary, metrics=save_metrics, checkpoint=epoch, settings=settings
        )

        if settings.keep_only_best_checkpoint:
            if model_improved or epoch == 1:
                if settings.verbose:
                    logger.info(f"Saving Model after epoch {epoch}")
                checkpoint_path = save_model(model=epoch_model, name=settings.name, path=settings.save_path)
            else:
                checkpoint_path = best_checkpoint_path
        else:
            if settings.verbose:
                logger.info(f"Saving Model after epoch {epoch}")
            checkpoint_path = save_model(model=epoch_model, name=settings.name + f"_{epoch}", path=settings.save_path)

        if model_improved or epoch == 1:
            best_checkpoint_path = checkpoint_path

    model = load_model(best_checkpoint_path)
    return model
