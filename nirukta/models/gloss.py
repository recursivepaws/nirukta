import re
from dataclasses import dataclass
from typing import Set, Union

from nirukta.inflection import Case, SanskritInflection
from nirukta.strings import find_nth

_TYPST_CMD_RE = re.compile(r"#\w+\(\)")


@dataclass
class EnglishGloss:
    """A single English gloss attached to a Sanskrit token.

    etymological=False  ->  [] translation gloss, shown in animations
    etymological=True   ->  {} etymology gloss, hidden by default
    """

    text: str

    def find_reference(
        self, english: str, visited: Set[tuple[int, int]]
    ) -> tuple[int, int]:
        typst_ranges = [(m.start(), m.end()) for m in _TYPST_CMD_RE.finditer(english)]

        n = 1
        while True:
            gi = find_nth(english, self.text, n)

            if gi < 0:
                raise ValueError(
                    "Gloss cannot reference text not contained in the english translation!\n"
                    + f'Tried to find "{self.text}" in "{english}" but was unable.'
                )

            index = (gi, gi + len(self.text))

            assert english[index[0] : index[1]] == self.text, (
                "Invalid gloss index into english text"
            )

            # Skip occurrences that land inside a Typst command like #linebreak()
            if any(start <= gi < end for start, end in typst_ranges):
                n += 1
                continue

            # If we've already found this instance of the gloss text
            if index in visited:
                n += 1
            else:
                return index


type EtymGloss = Union[SanskritInflection, Case]
type Gloss = Union[EnglishGloss, EtymGloss]
