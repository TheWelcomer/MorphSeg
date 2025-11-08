import torch
import numpy as np

from typing import List
from torch import Tensor
from model import LSTMModel
from util import make_mask_2d
from collections import namedtuple
from vocabulary import SequenceLabellingVocabulary

AlignmentPosition = namedtuple("AlignmentPosition", ["symbol", "predictions"])
Prediction = namedtuple("TransducerPrediction", ["prediction", "alignment"])


def _convert_idx(sources: List[List[str]], predictions: List[List[int]],
                 target_vocabulary: SequenceLabellingVocabulary, tau: int) -> List[Prediction]:
    aligned_predictions = []

    for source, prediction in zip(sources, predictions):
        prediction = np.array(prediction).reshape((-1, tau)).tolist()
        assert len(prediction) == len(source)

        alignment = []
        decoded_prediction = []
        for source_symbol, aligned_idx in zip(source, prediction):
            decoded_symbols = target_vocabulary.convert_idx(aligned_idx)
            decoded_symbols = [symbol for symbol in decoded_symbols if symbol != target_vocabulary.PAD_TOKEN]
            alignment.append(AlignmentPosition(symbol=source_symbol, predictions=decoded_symbols))
            decoded_prediction.extend(decoded_symbols)

        aligned_predictions.append(Prediction(prediction=decoded_prediction, alignment=alignment))

    return aligned_predictions


def argmax_decode(model: LSTMModel, logits: Tensor, lengths: Tensor, sources: List[List[str]],
                  target_vocabulary: SequenceLabellingVocabulary, tau: int) -> List[Prediction]:
    predictions = torch.argmax(logits, dim=-1).detach().cpu().tolist()
    lengths = (tau * lengths).detach().cpu().tolist()
    predictions = [prediction[:length] for prediction, length in zip(predictions, lengths)]

    return _convert_idx(sources=sources, predictions=predictions, target_vocabulary=target_vocabulary, tau=tau)


def viterbi_decode(model: LSTMModel, logits: Tensor, lengths: Tensor, sources: List[List[str]],
                   target_vocabulary: SequenceLabellingVocabulary, tau: int) -> List[Prediction]:
    lengths = tau * lengths
    # Get relevant dimension info
    batch, timesteps, num_tags = logits.shape

    # Apply log-softmax
    emission_scores = torch.log_softmax(logits, dim=-1)

    # Normalise transition and emission scores
    transition_scores = model.crf.transition_scores.T

    # Calculate prior
    prior = model.crf.prior.unsqueeze(0).expand(batch, num_tags)
    final_transition_scores = model.crf.final_transition_scores.unsqueeze(0).expand(batch, num_tags)

    # Start with emission scores at first time step times prior
    prev_alpha = emission_scores[:, 0, :].contiguous()
    prev_alpha = prior + prev_alpha
    alpha = [prev_alpha]

    # Initialise back-pointers
    back_pointers = torch.zeros(batch, timesteps, num_tags).long()

    # Forward recursion
    for t in range(1, timesteps):
        emission_scores_t = emission_scores[:, t, :]
        # Shape [Batch, 1, #Tags]
        prev_alpha = prev_alpha.unsqueeze(1)
        # Shape [Batch, #Tags, 1]

        alpha_t = prev_alpha + transition_scores
        # Shape [Batch, #Tags, #Tags]
        # Get maximum values for each tag
        alpha_t, back_pointers_t = torch.max(alpha_t, dim=2)
        alpha_t = alpha_t + emission_scores_t
        alpha.append(alpha_t)
        back_pointers[:, t, :] = back_pointers_t
        prev_alpha = alpha_t

    alpha = torch.stack(alpha)
    alpha = alpha.transpose(0, 1)

    viterbi_scores = alpha[torch.arange(batch), lengths - 1]
    viterbi_scores = viterbi_scores + final_transition_scores

    viterbi_scores, start_tag_indices = torch.max(viterbi_scores, dim=1)

    # Reconstruct predicted paths from back-pointers
    start_tag_indices = start_tag_indices.tolist()
    back_pointers = back_pointers.detach().cpu().numpy()
    predicted_paths = []

    for batch_idx, length in enumerate(lengths.tolist()):
        if length == 0:
            predicted_paths.append([])
            continue

        start_idx = start_tag_indices[batch_idx]
        predicted_path = [start_idx]

        for t in range(1, length):
            start_idx = back_pointers[batch_idx, length - t, start_idx].item()
            predicted_path.append(start_idx)

        predicted_path = list(reversed(predicted_path))
        try:
            assert len(predicted_path) == length
        except AssertionError:
            print(predicted_path)
            print(length)
            raise

        predicted_paths.append(predicted_path)

    # Decode predictions
    return _convert_idx(sources=sources, predictions=predicted_paths, target_vocabulary=target_vocabulary, tau=tau)


def ctc_crf_decode(model: LSTMModel, logits: Tensor, lengths: Tensor, sources: List[List[str]],
                   target_vocabulary: SequenceLabellingVocabulary, tau: int) -> List[Prediction]:
    # Prepare lengths (have to be multiplied by `tau` to account for length expansion)
    # and length mask (used later for masking padding)
    lengths = tau * lengths
    length_mask = make_mask_2d(lengths=lengths).to(logits.device)

    # Get relevant dimension info
    batch, timesteps, num_tags = logits.shape

    # Get relevant scores
    # Apply log softmax to prediction scores
    batch_emission_scores = torch.log_softmax(logits, dim=-1)
    # Get transition scores and expand batch dim
    transition_scores = model.crf.transition_scores.T
    batch_transition_scores = transition_scores.unsqueeze(0).expand(batch, num_tags, num_tags)
    # Get prior and expand batch dim
    prior = model.crf.prior
    batch_prior = prior.unsqueeze(0).expand(batch, num_tags)
    # Get final transition scores (probabilities that sequence ends with label) and expand batch and time dims
    final_transition_scores = model.crf.final_transition_scores
    batch_final_transition_scores = final_transition_scores.reshape((1, 1, -1)).expand(batch, timesteps, num_tags)

    # Initialise forward matrix for viterbi decoding and backpointers
    alpha = torch.empty(batch, 0, num_tags, device=batch_emission_scores.device)
    backpointers_time = []
    backpointers_label = []

    # Forward pass for viterbi decoding
    for t in range(timesteps):
        # Different from standard viterbi decoding, we have to account for blanks.
        # Blanks should not influence transition scores, therefore we need to find which is the best next
        # previous timestep where we don't predict a blank.
        #
        # We start with the case of only predicting blanks and the current timestep being the first
        # timestep where a non-blank label is predicted. In this case, the transition score is the label prior.
        blank_score = batch_emission_scores[:, :t, 0].sum(dim=1, keepdim=True).expand(batch, num_tags)
        alpha_t = batch_emission_scores[:, t] + batch_prior + blank_score
        # Initialise backpointers
        best_prev_label = torch.full((batch, num_tags,), fill_value=-1, dtype=torch.long, device=alpha.device)
        best_prev_timestep = torch.full((batch, num_tags,), fill_value=-1, dtype=torch.long, device=alpha.device)

        # In the first timestep (t=0), we cannot recur to any previously predicted tags, therefore skip
        if t > 0:
            # For each timestep 0 <= s < t get the score of predicting blanks at timesteps s+1, s+2, ..., t-1
            # This can be written as \sum_{k=s+1}^{t} p_k(0) = \sum_{k=0}^{t} p_k(0) - \sum_{k=0}^{s} p_k(0)
            blank_scores_cum = batch_emission_scores[:, :t, 0].cumsum(dim=1)
            blank_scores = blank_scores_cum[:, -1].unsqueeze(1).expand(batch, t)
            blank_scores = blank_scores - blank_scores_cum

            # Calculate scores for all combinations of tag l1, previous tag l2, and previous timestep s.
            # The score is given by the sum of
            # viterbi score at previous tag PLUS predicting blank at s+1, s+2, ..., t PLUS probability of predicting
            # tag l1 at timestep t PLUS transition probability form previous tag l2 to tag l1
            # Note that all calculations are sums because we are operating in log space
            #
            # The resulting sums (scores) are stored in the following tensor of shape [batch x t x #tags x #tags]
            scores = (
                    alpha.unsqueeze(3).expand(batch, t, num_tags, num_tags) +
                    blank_scores.reshape(batch, t, 1, 1).expand(batch, t, num_tags, num_tags) +
                    batch_emission_scores[:, t].reshape(batch, 1, 1, num_tags).expand(batch, t, num_tags, num_tags) +
                    batch_transition_scores.unsqueeze(1).expand(batch, t, num_tags, num_tags)
            )

            # Get the best previous timesteps
            scores, s = torch.max(scores, dim=1)
            # Get the best previous labels
            scores, prev_label = torch.max(scores, dim=1)
            # Filter out irrelevant labels of the best previous timesteps
            s = torch.gather(s, index=prev_label.unsqueeze(1), dim=1).squeeze(1)

            # Compare best scores to case where current timestep yields the first non-blank prediction
            superior_idx = torch.nonzero(scores > alpha_t, as_tuple=True)
            # Update viterbi scores and backpointers
            alpha_t[superior_idx] = scores[superior_idx]
            best_prev_label[superior_idx] = prev_label[superior_idx]
            best_prev_timestep[superior_idx] = s[superior_idx]

        # Save viterbi scores and backpointers
        alpha = torch.cat([alpha, alpha_t.reshape(batch, 1, num_tags)], dim=1)
        backpointers_time.append(best_prev_timestep.detach().cpu().tolist())
        backpointers_label.append(best_prev_label.detach().cpu().tolist())

    # Next, we have to account for final transition scores
    # (the probabilities that a certain tag is the last predicted tag).
    # The score of each tag at timestep t being the last tag is given as
    # viterbi score of the tag at timestep t PLUS final transition score of tag PLUS score of predicting blanks at
    # timesteps t+1, t+2, ..., T
    #
    # Calculate scores for predicting blanks for all timesteps t.
    # We use the same "total sum - cumulative sum" trick as above.
    blank_scores_cum = batch_emission_scores[:, :, 0].cumsum(dim=1)
    # However, we have to take into account that sequences of batch elements have different lengths
    blank_scores_final = blank_scores_cum[torch.arange(batch), lengths-1]
    blank_scores_final = blank_scores_final.unsqueeze(1).expand(batch, timesteps)
    blank_scores = blank_scores_final - blank_scores_cum
    # Next, we mask padding to avoid selecting illegal timesteps.
    blank_scores = torch.masked_fill(blank_scores, mask=length_mask, value=-torch.inf)
    # Blank prediction scores do not depend on the tag, so we can simply copy
    blank_scores = blank_scores.unsqueeze(2).expand(batch, timesteps, num_tags)
    # Calculate scores as described above
    final_scores = alpha + batch_final_transition_scores + blank_scores

    # Get the best final timestep and tag for all batch elements
    final_scores, best_end_timestep = torch.max(final_scores, dim=1)
    best_score, best_end_label = torch.max(final_scores, dim=1)
    best_end_timestep = best_end_timestep[torch.arange(batch), best_end_label]

    best_end_label = best_end_label.cpu().tolist()
    best_end_timestep = best_end_timestep.cpu().tolist()
    lengths = lengths.cpu().tolist()

    # Follow backpointers to get predicted tags for each batch element
    predicted_paths = []

    for batch_elem_id, (length, end_label, end_timestep) in enumerate(zip(lengths, best_end_label, best_end_timestep)):
        predicted_path = [0 for _ in range(length)]
        label = end_label
        timestep = end_timestep

        while timestep != -1:
            predicted_path[timestep] = label
            timestep, label = (
                backpointers_time[timestep][batch_elem_id][label],
                backpointers_label[timestep][batch_elem_id][label]
            )

        predicted_paths.append(predicted_path)

    # Decode predictions
    return _convert_idx(sources=sources, predictions=predicted_paths, target_vocabulary=target_vocabulary, tau=tau)
