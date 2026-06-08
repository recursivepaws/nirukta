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

    def meter_slp1(self):
        slp1 = ""
        for line in self.lines:
            for vAkya in line.vAkyAni:
                for token in vAkya.tokens:
                    # TODO: Ignore other key starter phrases
                    # like 'SrI BagavAn uvAca'
                    if slp1 == "" and token.slp1 == "oM":
                        continue
                    else:
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
