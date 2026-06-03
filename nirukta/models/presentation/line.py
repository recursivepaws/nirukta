from dataclasses import dataclass
from typing import List

from nirukta.models.presentation.utterance import Utterance
from nirukta.models.presentation.akshara import _SLP1_VOWELS, _SLP1_ENDS_CLEANLY


@dataclass
class Line:
    """A stanza-level grouping of verse lines (between --- line --- markers)."""

    vAkyAni: List[Utterance]

    def slp1(self) -> str:
        result = ""
        for i, utterance in enumerate(self.vAkyAni):
            result += utterance.slp1()

            if i + 1 < len(self.vAkyAni):
                last = utterance.slp1()[-1]
                nxt = self.vAkyAni[i + 1].slp1()[0]

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
