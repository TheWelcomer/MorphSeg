import pandas as pd
import os

def sent2rules_strict(source, target):
    if len(source) == 0:
        return [], []

    # Build edit distance matrix
    m, n = len(source), len(target)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Track which operation led to each cell
    backtrack = [[None] * (n + 1) for _ in range(m + 1)]

    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
        if i > 0:
            backtrack[i][0] = 'DEL'

    for j in range(n + 1):
        dp[0][j] = j
        if j > 0:
            backtrack[0][j] = 'INS'

    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if source[i - 1] == target[j - 1]:
                # Match
                dp[i][j] = dp[i - 1][j - 1]
                backtrack[i][j] = 'MATCH'
            else:
                delete_cost = dp[i - 1][j] + 1
                insert_cost = dp[i][j - 1] + 1
                replace_cost = dp[i - 1][j - 1] + 1

                min_cost = min(delete_cost, insert_cost, replace_cost)
                dp[i][j] = min_cost

                if min_cost == delete_cost:
                    backtrack[i][j] = 'DEL'
                elif min_cost == insert_cost:
                    backtrack[i][j] = 'INS'
                else:
                    backtrack[i][j] = 'REP'

    # Backtrack and assign ALL target chars to source positions
    actions = [[] for _ in range(len(source))]  # List of chars for each source pos
    i, j = m, n

    while i > 0 or j > 0:
        op = backtrack[i][j]

        if op == 'MATCH':
            # Source char i-1 outputs target char j-1 (copy)
            actions[i - 1].insert(0, ('COPY', source[i - 1]))
            i -= 1
            j -= 1
        elif op == 'REP':
            # Source char i-1 outputs target char j-1 (replace)
            actions[i - 1].insert(0, ('OUT', target[j - 1]))
            i -= 1
            j -= 1
        elif op == 'DEL':
            # Source char i-1 outputs nothing (will be marked for deletion later)
            i -= 1
        elif op == 'INS':
            # Target char j-1 needs to be inserted - attach to previous source pos
            attach_pos = max(0, i - 1)
            actions[attach_pos].insert(0, ('OUT', target[j - 1]))
            j -= 1

    # Convert to final action strings
    final_actions = []
    for i, char_actions in enumerate(actions):
        if not char_actions:
            final_actions.append('DELETE')
        else:
            # Build output string
            output_parts = []
            has_copy = False
            for op, char in char_actions:
                if op == 'COPY':
                    has_copy = True
                    output_parts.append(char)
                else:
                    output_parts.append(char)

            output_str = ''.join(output_parts)
            if has_copy and len(output_parts) == 1:
                final_actions.append('COPY')
            else:
                final_actions.append(output_str)

    input_chars = list(source)
    return input_chars, final_actions


def rules2sent_strict(source, actions):
    """
    Decode: each action applies to exactly one source character.
    """
    if len(source) == 0:
        return ""

    target = []

    for char, action in zip(source, actions):
        if action == 'COPY':
            target.append(char)
        elif action == 'DELETE':
            pass
        else:
            target.append(action)

    return ''.join(target)


# Comprehensive test suite
def run_oracle(lang, split):
    print(f"Running oracle for language: {lang}, split: {split}")
    label_set = set()
    sources = []
    targets = []
    data_set = pd.read_csv(f'data/raw_data/{lang}/{split}.tsv', sep='\t')
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
            input_chars, actions = sent2rules_strict(source, target)
            reconstructed = rules2sent_strict(source, actions)
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
    if not os.path.exists(f'data/processed_data/{lang}'):
        os.makedirs(f'data/processed_data/{lang}')
    df.to_csv(f'data/processed_data/{lang}/{split}.csv', index=False)


if __name__ == "__main__":
    run_oracle("eng", "train")
