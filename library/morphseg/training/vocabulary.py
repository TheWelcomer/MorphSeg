from __future__ import annotations

from typing import List


class SequenceLabellingVocabulary:
    PAD_TOKEN = "<PAD>"
    UNK_TOKEN = "<UNK>"

    def __init__(self, symbols: List[str]) -> None:
        self.specials = self.get_specials()
        self.alphabet = self.specials + list(sorted(symbols))

        self.token2idx = {token: idx for idx, token in enumerate(self.alphabet)}
        self.idx2token = {idx: token for idx, token in enumerate(self.alphabet)}

        self.unk_idx = self.token2idx[self.UNK_TOKEN]

    def get_specials(self) -> List[str]:
        return [self.PAD_TOKEN, self.UNK_TOKEN]

    def __len__(self):
        return len(self.alphabet)

    def __getitem__(self, idx: int) -> str:
        return self.alphabet[idx]

    def is_special(self, token: str):
        return token in self.specials

    def index_sequence(self, tokens: List[str]) -> List[int]:
        return [self.token2idx.get(token, self.unk_idx) for token in tokens]

    def convert_idx(self, idx: List[int]) -> List[str]:
        return [self.idx2token.get(index, self.UNK_TOKEN) for index in idx]

    @classmethod
    def build_vocabulary(cls, sequences: List[List[str]]) -> SequenceLabellingVocabulary:
        all_tokens = list(set.union(*(set(sequence) for sequence in sequences)))
        return cls(symbols=all_tokens)
