from dataclasses import dataclass

from janim.imports import (
    FadeOut,
    Succession,
    Timeline,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import LATIN_FONT
from nirukta.models import Language, Sloka
from nirukta.render import set_font, typst_code
from nirukta.typst import arrange_vertical
from nirukta.util import SCALE


@dataclass
class EnglishTimeline(Timeline):
    sloka: Sloka

    def __init__(self, sloka: Sloka):
        super().__init__()
        self.sloka = sloka

    def construct(self):
        rows = []

        for line in self.sloka.lines:
            for vAkya in line.vAkyAni:
                rows.append(typst_code(vAkya.english, Language.ENGLISH))

            # Add an empty row between lines
            rows.append(typst_code("", Language.ENGLISH))

        print(f"there are {len(rows)} rows in the english text")
        print(f"{rows}")

        grid = arrange_vertical(list(map(lambda code: f"[{code}]", rows)), gutter=0.6)

        group = TypstText(
            set_font(grid, LATIN_FONT),
            scale=SCALE,
        )

        self.play(
            Succession(
                Write(group, duration=2.0), Wait(2.0), FadeOut(group, duration=0.5)
            )
        )
