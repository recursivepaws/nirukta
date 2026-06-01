from dataclasses import dataclass, field
from typing import List, Union

from nirukta.models.enums import SoundChange
from nirukta.models.tokens.simple import SimpleToken


type SimpleOrCompound = Union[SimpleToken, CompoundToken]


@dataclass
class CompoundToken:
    """A sandhi compound.

    parts   -- ordered list of SimpleToken / CompoundToken (the components)
    slp1 -- the phonetically-merged SLP1 surface form (after '=')
    """

    parts: List[SimpleOrCompound]
    slp1: str


@dataclass
class SoundChangeToken:
    part: SimpleOrCompound
    slp1: str
    kind: SoundChange

    def as_compound(self) -> CompoundToken:
        return CompoundToken([self.part], self.slp1)
