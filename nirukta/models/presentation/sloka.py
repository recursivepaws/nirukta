from dataclasses import dataclass
from typing import List, Optional

from nirukta.constants import DIGITS_RE

from nirukta.models.presentation.line import Line

from skrutable.meter_identification import MeterIdentifier
MI = MeterIdentifier()

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
                        slp1 += token.slp1 + " "

        slp1 += "\n"
        return slp1

    def meter(self):
        verse = MI.identify_meter(self.slp1(), from_scheme='SLP')
        # print(list(map(lambda x: x.split(''), )))
        weight_lines = verse.syllable_weights.split('\n')
        text_lines = verse.text_syllabified.split('\n')

        tups = []
        padas = []
        for li in range(len(text_lines)):
            line_sounds = list(filter(lambda x: len(x) > 0, text_lines[li].split(' ')))
            print(line_sounds)
            print(weight_lines[li])
            for si in range(len(line_sounds)):
                tups.append((line_sounds[si], weight_lines[li][si]))

            padas.append(tups)
            tups = []

        # list(map(lambda x: x.split(' '), text_lines))
        #
        # print(verse.text_syllabified.split('\n'))
        #
        print(verse.meter_label)
        print(padas)
        return ((verse.meter_label, padas))
        # print(verse.summarize())
