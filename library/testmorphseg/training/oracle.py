import pandas as pd
import os

import collections


def sent2rules(source: str, target: str) -> tuple[list[str], list[str]]:
    """
    Generates a sequence of action labels to transform a source word into its
    target morphological segmentation using an enhanced alignment algorithm.

    This oracle is designed to produce a minimal and consistent set of labels
    for training a sequence labeling model. It uses a modified Needleman-Wunsch
    algorithm that, in case of alignment ties, prefers alignments with longer
    contiguous copied segments, as described in Girrbach (2022).

    The generated labels are structured, e.g., 'COPY', 'DELETE', '@@+COPY', 'COPY+e'.

    Args:
        source: The source word.
        target: The target segmented string.

    Returns:
        A tuple containing:
        - A list of characters from the source word.
        - A list of corresponding action labels.
    """
    m, n = len(source), len(target)

    # DP table stores tuples of: (match_count, sum_of_squared_lengths, current_contiguous_len)
    # We want to maximize match_count, then sum_of_squared_lengths.
    dp = [[(-1, -1, -1)] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = (0, 0, 0)

    # Backtrack table stores the operation ('MATCH', 'INS', 'DEL') that led to the optimal score.
    backtrack = [[None] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                continue

            # --- Calculate potential scores from three possible previous cells ---
            candidates = []

            # 1. Deletion (from dp[i-1][j])
            if i > 0:
                score, sum_sq, _ = dp[i - 1][j]
                # Reset contiguous length on a gap
                candidates.append(((score, sum_sq, 0), 'DEL'))

            # 2. Insertion (from dp[i][j-1])
            if j > 0:
                score, sum_sq, _ = dp[i][j - 1]
                # Reset contiguous length on a gap
                candidates.append(((score, sum_sq, 0), 'INS'))

            # 3. Match (from dp[i-1][j-1])
            if i > 0 and j > 0 and source[i - 1] == target[j - 1]:
                score, sum_sq, contig_len = dp[i - 1][j - 1]
                new_contig_len = contig_len + 1
                # Update sum of squares: remove old square, add new one
                new_sum_sq = sum_sq - (contig_len ** 2) + (new_contig_len ** 2)
                candidates.append(((score + 1, new_sum_sq, new_contig_len), 'MATCH'))

            # --- Tie-breaking: Choose the best candidate ---
            # Sort first by match_count (primary), then sum_of_squared_lengths (secondary)
            candidates.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)

            if candidates:
                best_score, best_op = candidates[0]
                dp[i][j] = best_score
                backtrack[i][j] = best_op

    # --- Backtrack to get alignment and generate intermediate actions ---
    actions = collections.defaultdict(list)
    i, j = m, n
    while i > 0 or j > 0:
        op = backtrack[i][j]
        if op == 'MATCH':
            i -= 1
            j -= 1
            # ('COPY', char) indicates the character at this position was copied
            actions[i].insert(0, ('COPY', source[i]))
        elif op == 'DEL':
            i -= 1
            # Deletions are handled by the absence of other actions
        elif op == 'INS':
            j -= 1
            # ('OUT', char) attaches an inserted character to the previous source position
            attach_pos = max(0, i - 1)
            actions[attach_pos].insert(0, ('OUT', target[j]))
        else:  # Should not happen in a valid alignment
            raise Exception("Invalid state in backtracking")

    # --- Convert intermediate actions into final, structured string labels ---
    final_actions = []
    for i in range(m):
        char_actions = actions.get(i, [])

        if not char_actions:
            final_actions.append('DELETE')
            continue

        try:
            # Find where the source character itself is copied
            copy_index = [op for op, char in char_actions].index('COPY')
        except ValueError:
            # This source character was replaced entirely
            output_str = "".join([char for op, char in char_actions])
            final_actions.append(output_str)
            continue

        # Build label from prefix, COPY marker, and suffix
        prefix = "".join([char for op, char in char_actions[:copy_index]])
        suffix = "".join([char for op, char in char_actions[copy_index + 1:]])

        label_parts = []
        if prefix:
            label_parts.append(prefix)

        # Use 'COPY' as the standard representation for the copied character
        label_parts.append('COPY')

        if suffix:
            label_parts.append(suffix)

        final_actions.append("+".join(label_parts))

    return list(source), final_actions
# Comprehensive test suite

def rules2sent(source: str, actions: list[str]) -> str:
    """
    Reconstructs the target morpheme string from a source word and a sequence
    of structured action labels.

    This function is the inverse of the `sent2rules` oracle. It correctly
    interprets labels like 'COPY', 'DELETE', '@@+COPY', and 'COPY+e'.

    Args:
        source: The source word.
        actions: The list of action labels corresponding to each source character.

    Returns:
        The reconstructed target string.
    """
    if len(source) != len(actions):
        raise ValueError("Length of source and actions must be equal.")

    target_parts = []
    for char, action in zip(source, actions):
        if action == 'DELETE':
            continue

        # Split the action label by '+' to handle compound operations
        action_parts = action.split('+')

        output_for_char = []
        for part in action_parts:
            if part == 'COPY':
                output_for_char.append(char)
            else:
                # This part is a literal string to be inserted/substituted
                output_for_char.append(part)

        target_parts.append("".join(output_for_char))

    return "".join(target_parts)

def run_oracle(lang, split):
    print(f"Running oracle for language: {lang}, split: {split}")
    label_set = set()
    sources = []
    targets = []
    data_set = pd.read_csv(f'data/{lang}/{split}.tsv', sep='\t')
    test_cases = list(data_set.itertuples(index=False))

    passed = 0
    failed = 0
    non_string_skip = 0
    empty_source_skip = 0

    for tuple in test_cases:
        source = tuple[0]
        target = tuple[1]

        # Skip non-string cases
        if type(source) is not str or type(target) is not str:
            non_string_skip += 1
            continue

        # Skip empty source cases
        if len(source) == 0:
            empty_source_skip += 1
            continue

        try:
            input_chars, actions = sent2rules(source, target)
            reconstructed = rules2sent(source, actions)
            sources.append(input_chars)
            targets.append(actions)
            for action in actions:
                label_set.add(action)

            # Verify invariants
            assert len(input_chars) == len(source), "Input length mismatch"
            assert len(actions) == len(source), "Action length mismatch"
            assert reconstructed == target, f"Reconstruction failed: got '{reconstructed}', expected '{target}'"

            # Verify each source char gets exactly one action
            for i, (char, action) in enumerate(zip(input_chars, actions)):
                assert char == source[i], f"Input char mismatch at position {i}"

            # print(f"✓ PASS")
            # print(f"  Source: '{source}' → Target: '{target}'")
            # print(f"  Actions: {actions[:10]}{'...' if len(actions) > 10 else ''}")
            # print()
            passed += 1

        except Exception as e:
            # print(f"✗ FAIL")
            # print(f"  Source: '{source}' → Target: '{target}'")
            # print(f"  Error: {e}")
            # print()
            failed += 1

    # Label Set
    # print("=" * 80)
    # print("LABEL SET")
    # print("=" * 80)
    # print(sorted(label_set))
    # print(f"Total unique labels: {len(label_set)}")
    # print("=" * 80)

    # Summary
    print("=" * 80)
    print(f"{lang.upper()} - {split.upper()} SET ACTION LABEL GENERATION RESULTS")
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"# Non-String Entries (Skipped): {non_string_skip}")
    print(f"# Empty Source Entries (Skipped): {empty_source_skip}")
    print(f"Total unique labels: {len(label_set)}")
    print(
        f"Success rate: {passed}/{passed + failed} ({100 * passed / (passed + failed) if passed + failed > 0 else 0:.1f}%)")
    print("=" * 80)

    df = pd.DataFrame({'source': sources, 'actions': targets})
    # if split == "train":
    #     df = df[:50000]
    # if split == "test":
    #     df = df[:10000]
    if not os.path.exists(f'data/processed_data/{lang}'):
        os.makedirs(f'data/processed_data/{lang}')
    df.to_csv(f'data/processed_data/{lang}/{split}.csv', index=False)


if __name__ == "__main__":
    run_oracle("en", "train")
