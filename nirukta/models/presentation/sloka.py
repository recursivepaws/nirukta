from dataclasses import dataclass

from typing import List, Optional

from nirukta.constants import DIGITS_RE
from nirukta.models.tokens.punctuation import PunctuationToken
from nirukta.render import transliterate

from nirukta.models.presentation.akshara import Akshara, identify
from nirukta.models.presentation.line import Line
from nirukta.models.enums import System


@dataclass
class Sloka:
    """"""

    lines: List[Line]
    number: Optional[int]

    def __init__(self, lines: List[Line]) -> None:
        number = None
        for line in list(lines):
            for vAyka in line.vAkyAni:
                for token in vAyka.tokens:
                    if isinstance(token, PunctuationToken):
                        if match := DIGITS_RE.search(token.slp1):
                            number = int(match.group())
        self.lines = lines
        self.number = number

        pass

    def preview(self, length: int = 60) -> str:
        # first utterance's english, truncated, for menu/list labels
        if self.lines and self.lines[0].vAkyAni:
            return self.lines[0].vAkyAni[0].english.strip()[:length]
        return ""

    def meter_slp1(self):
        slp1 = ""
        for line in self.lines:
            if not line.skip():
                for vAkya in line.vAkyAni:
                    for token in vAkya.tokens:
                        slp1 += token.slp1 + " "

        slp1 += "\n"
        return slp1

    def meter(self) -> tuple[str, List[List[Akshara]]]:
        verse = identify(self.meter_slp1(), from_scheme="SLP")
        weight_lines = verse.syllable_weights.split("\n")
        text_lines = verse.text_syllabified.split("\n")

        padas: List[List[Akshara]] = []
        for li in range(len(text_lines)):
            line_sounds = list(filter(lambda x: len(x) > 0, text_lines[li].split(" ")))
            aksharas: List[Akshara] = []
            for si in range(len(line_sounds)):
                aksharas.append(
                    Akshara(text=line_sounds[si], weight=weight_lines[li][si])
                )
            padas.append(aksharas)

        # Display custom label for unknown meters
        if verse.meter_label == "na":
            verse.meter_label = "ajYAtavftta"

        label = transliterate(System.IAST, System.SLP1, verse.meter_label)
        label = label.split(" ")[0].strip()

        return (label, padas)

    def english_typst(self) -> List[str]:
        english = []
        for line in self.lines:
            el = ""
            for vAkya in line.vAkyAni:
                el += vAkya.english + "\n"
            english.append(el)

        return english

        # rows = []
        #
        # for line in self.lines:
        #     english = ""
        #     for vAkya in line.vAkyAni:
        #         english += vAkya.english + "#linebreak()"
        #
        #     rows.append(typst_code(english, Language.ENGLISH))
        #
        # return
        # return arrange_vertical(rows, gutter=0.6)


def sloka_label(index: int, sloka: Sloka) -> str:
    # shared label for sloka menus/lists (GUI picker and CLI)
    num = f"#{sloka.number} — " if sloka.number is not None else f"{index + 1}. "
    return f"{num}{sloka.preview()}"
