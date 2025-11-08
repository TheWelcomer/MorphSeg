import torch

from torch import Tensor
from dataset import Batch
from model import LSTMModel
from util import make_mask_2d
from collections import namedtuple
from torch.nn.functional import cross_entropy
from torch.nn.functional import ctc_loss as ctc

ModelOutput = namedtuple("ModelOutput", field_names=["loss", "logits"])


def _get_logits(model: LSTMModel, batch: Batch) -> Tensor:
    return model(
        inputs=batch.sources, lengths=batch.source_lengths,
        features=batch.features, feature_lengths=batch.feature_lengths
    )


def cross_entropy_loss(model: LSTMModel, batch: Batch, reduction: str = "mean") -> ModelOutput:
    logits = _get_logits(model=model, batch=batch)
    flattened_logits = torch.flatten(logits, end_dim=-2)
    flattened_targets = torch.flatten(batch.targets).to(logits.device)
    loss = cross_entropy(flattened_logits, flattened_targets, ignore_index=0, reduction=reduction)
    return ModelOutput(loss=loss, logits=logits)


def ctc_loss(model: LSTMModel, batch: Batch, reduction: str = "mean") -> ModelOutput:
    logits = _get_logits(model=model, batch=batch)
    log_probs = torch.log_softmax(logits, dim=-1)
    log_probs = torch.transpose(log_probs, 0, 1)
    targets = batch.targets.to(logits.device)
    tau = model.tau
    loss = ctc(
        log_probs=log_probs, targets=targets, input_lengths=tau * batch.source_lengths,
        target_lengths=batch.target_lengths, blank=0, reduction=reduction
    )
    return ModelOutput(loss=loss, logits=logits)


def crf_loss(model: LSTMModel, batch: Batch, reduction: str = "mean") -> ModelOutput:
    logits = _get_logits(model=model, batch=batch)
    targets = batch.targets.to(logits.device)
    # emission scores shape: batch x timesteps x #labels
    # tags: batch x timesteps

    batch_size = logits.shape[0]

    # Apply log-softmax
    emission_scores = torch.log_softmax(logits, dim=-1)

    # Extract emission scores
    tag_index = targets.unsqueeze(2)
    emission_scores = torch.gather(emission_scores, index=tag_index, dim=2)
    emission_scores = emission_scores.squeeze(2)
    # Shape [Batch, Timesteps]

    # Extract transition scores
    transition_scores = model.crf.get_transition_scores(batch.targets)

    # Extract prior
    prior = model.crf.prior[batch.targets[:, 0]].contiguous()
    prior = prior.reshape((batch_size, 1))

    # Combine prior and transition scores
    transition_scores = torch.cat([prior, transition_scores], dim=1)

    # Calculate transition probabilities to stop tag
    length_index = (batch.target_lengths - 1).unsqueeze(1).to(emission_scores.device)
    final_tags = torch.gather(targets, index=length_index, dim=1)
    final_tags = final_tags.flatten()
    final_transition_scores = model.crf.final_transition_scores[final_tags]
    final_transition_scores = final_transition_scores.contiguous()

    # Calculate path probabilities
    nll = transition_scores + emission_scores
    # Mask padding
    mask = make_mask_2d(batch.source_lengths).to(emission_scores.device)
    nll = torch.masked_fill(nll, mask=mask, value=0.0)

    # Sum tag scores for each sequence
    # Add transition probabilities to stop tag
    nll = -(torch.sum(nll, dim=1) + final_transition_scores)

    if reduction == "mean":
        nll = torch.mean(nll, dim=0)
    elif reduction == "sum":
        nll = torch.sum(nll, dim=0)
    elif reduction == "none":
        pass
    else:
        raise ValueError(f"Unknown reduction: {reduction}")

    return ModelOutput(loss=nll, logits=logits)


def ctc_crf_loss(model: LSTMModel, batch: Batch, reduction: str = "mean") -> ModelOutput:
    # Get prediction log-probs
    logits = _get_logits(model=model, batch=batch)
    scores = torch.log_softmax(logits, dim=-1)
    source_lengths = model.tau * batch.source_lengths

    # Save constants
    batch_size = scores.shape[0]
    source_length = scores.shape[1]
    target_length = batch.targets.shape[1]
    batch_indexer = torch.arange(batch_size)
    neg_inf_score = -1e8
    neg_inf_array = torch.full((batch_size, 1), fill_value=neg_inf_score, device=scores.device)

    # Extract prior
    prior = model.crf.prior[batch.targets[:, 0]].contiguous()
    prior = prior.reshape((batch_size, 1))

    # Extract transition_scores
    transition_scores = model.crf.get_transition_scores(batch.targets)
    transition_scores = torch.cat([neg_inf_array, prior, transition_scores], dim=1)

    alpha = []
    alpha_0 = torch.cat(
        [
            torch.zeros(batch_size, 1, device=scores.device),
            torch.full((batch_size, target_length), fill_value=neg_inf_score, device=scores.device)
        ],
        dim=1
    )
    alpha.append(alpha_0)

    for t in range(1, source_length+1):
        prev_alpha = alpha[-1]
        blank_scores_t = scores[:, t-1, 0].unsqueeze(1).expand(batch_size, target_length+1)
        scores_t = scores[:, t-1, :].gather(dim=-1, index=batch.targets.to(scores.device))
        prediction_scores_t = torch.cat([neg_inf_array, scores_t], dim=1)

        blank_transition_score = prev_alpha + blank_scores_t
        prediction_transition_score = torch.cat([neg_inf_array, prev_alpha[:, :-1]], dim=1)
        prediction_transition_score = prediction_transition_score + prediction_scores_t + transition_scores

        alpha_t = torch.logsumexp(torch.stack([blank_transition_score, prediction_transition_score]), dim=0)
        # alpha_t = prediction_transition_score
        alpha.append(alpha_t)

    alpha = torch.stack(alpha)
    alpha = alpha.transpose(0, 1)

    log_likelihoods = alpha[batch_indexer, source_lengths, batch.target_lengths]
    log_likelihoods = log_likelihoods.flatten().contiguous()

    # Calculate transition probabilities to stop tag
    length_index = (batch.target_lengths - 1).unsqueeze(1).to(scores.device)
    final_tags = torch.gather(batch.targets.to(scores.device), index=length_index, dim=1)
    final_tags = final_tags.flatten()
    final_transition_scores = model.crf.final_transition_scores[final_tags]
    final_transition_scores = final_transition_scores.contiguous()

    nll = -(log_likelihoods + final_transition_scores)

    if reduction == "mean":
        nll = torch.mean(nll, dim=0)
    elif reduction == "sum":
        nll = torch.sum(nll, dim=0)
    elif reduction == "none":
        pass
    else:
        raise ValueError(f"Unknown reduction: {reduction}")

    return ModelOutput(loss=nll, logits=logits)
