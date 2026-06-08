from dataclasses import dataclass
from typing import Sequence

from nirukta.models.tokens import TokenType, skip_spaces_token


@dataclass
class Utterance:
    """One sentence-worth of Sanskrit tokens paired with its English rendering."""

    tokens: Sequence[TokenType]
    english: str

    def slp1(self) -> str:
        result = ""
        for i, token in enumerate(self.tokens):
            result += token.slp1

            if i + 1 < len(self.tokens):
                next = self.tokens[i + 1]
                if skip_spaces_token(token, next):
                    # Do not break aksharas
                    pass
                else:
                    result += " "
        return result
