from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from nirukta.models.enums import SoundChange

if TYPE_CHECKING:
    from nirukta.models.tokens.token import TokenType


@dataclass
class CompoundToken:
    """A sandhi compound.

    parts   -- ordered list of SimpleToken / CompoundToken (the components)
    slp1 -- the phonetically-merged SLP1 surface form (after '=')
    """

    parts: Sequence[TokenType]
    slp1: str


@dataclass
class SoundChangeToken:
    part: TokenType
    slp1: str
    kind: SoundChange

    def as_compound(self) -> CompoundToken:
        return CompoundToken([self.part], self.slp1)
