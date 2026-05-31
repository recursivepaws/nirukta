from dataclasses import dataclass

import json
from typing import List, Optional

from nirukta.constants import DIGITS_RE
from nirukta.render import transliterate
from janim.logger import log

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
                    if isinstance(token, str):
                        if match := DIGITS_RE.search(token):
                            number = int(match.group())
        self.lines = lines
        self.number = number

        pass

    def slp1(self):
        slp1 = ""
        for line in self.lines:
            for vAkya in line.vAkyAni:
                for token in vAkya.tokens:
                    if isinstance(token, str):
                        slp1 += token
                    else:
                        if slp1 == "" and token.slp1 == "oM":
                            continue
                        else:
                            slp1 += token.slp1 + " "

        slp1 += "\n"
        return slp1

    def meter(self) -> tuple[str, List[List[Akshara]]]:
        verse = identify(self.slp1(), from_scheme="SLP")
        # print(list(map(lambda x: x.split(''), )))
        weight_lines = verse.syllable_weights.split("\n")
        text_lines = verse.text_syllabified.split("\n")

        padas: List[List[Akshara]] = []
        for li in range(len(text_lines)):
            line_sounds = list(filter(lambda x: len(x) > 0, text_lines[li].split(" ")))
            # print(line_sounds)
            # print(weight_lines[li])

            aksharas: List[Akshara] = []
            for si in range(len(line_sounds)):
                aksharas.append(
                    Akshara(text=line_sounds[si], weight=weight_lines[li][si])
                )
            padas.append(aksharas)

        # log.info(f"verse meter: {json.dumps(verse)}")

        label = transliterate(System.IAST, System.SLP1, verse.meter_label)
        assert label is not None

        # if "(" in label:
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
