from dataclasses import dataclass
from typing import List

from nirukta.models.presentation.utterance import Utterance
from nirukta.models.tokens import skip_spaces_str


@dataclass
class Line:
    """A stanza-level grouping of verse lines (between --- line --- markers)."""

    vAkyAni: List[Utterance]

    def slp1(self) -> str:
        result = ""
        for i, utterance in enumerate(self.vAkyAni):
            result += utterance.slp1()

            if i + 1 < len(self.vAkyAni):
                if skip_spaces_str(utterance.slp1(), self.vAkyAni[i + 1].slp1()):
                    # Do not break aksharas
                    pass
                else:
                    result += " "
        return result
