from dataclasses import dataclass
from typing import List

from nirukta.models.tokens import TokenType
from nirukta.models.presentation.akshara import (
    _SLP1_VOWELS,
    _SLP1_ENDS_CLEANLY,
)


# TODO: rewrite the whole TokenType thing to do away
# with this silly `str` thing.
def _last_char(token: TokenType) -> str | None:
    if isinstance(token, str):
        return None
    return token.slp1[-1] if token.slp1 else None


def _first_char(token: TokenType) -> str | None:
    if isinstance(token, str):
        return None
    return token.slp1[0] if token.slp1 else None


@dataclass
class Utterance:
    """One sentence-worth of Sanskrit tokens paired with its English rendering."""

    tokens: List[TokenType]
    english: str

    def slp1(self) -> str:
        result = ""
        for i, token in enumerate(self.tokens):
            result += token if isinstance(token, str) else token.slp1
            if i + 1 < len(self.tokens):
                last = _last_char(token)
                nxt = _first_char(self.tokens[i + 1])
                if (
                    last is not None
                    and nxt is not None
                    and last not in _SLP1_ENDS_CLEANLY
                    and nxt in _SLP1_VOWELS
                ):
                    # Do not break aksharas
                    pass
                else:
                    result += " "
        return result
