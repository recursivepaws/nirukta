from pathlib import Path
from typing import Optional

import vidyut
from janim.imports import DOWN, YELLOW, FadeOut, Group, Timeline, TypstText, Wait, Write
from vidyut.chandas import Chandas

from nirukta.constants import INTRO_FONT, SCALE
from nirukta.models import Language, Sloka
from nirukta.render import FlatAligned, set_font, sloka_group, sloka_group_chandas, typst_code
from nirukta.timelines.transform import LenientTransformMatchingDiff

_DATA_DIR = Path(__file__).parents[2] / "vidyut_data"
_METERS_TSV = _DATA_DIR / "chandas" / "meters.tsv"


def _get_chandas() -> Chandas:
    if not _METERS_TSV.exists():
        _DATA_DIR.mkdir(exist_ok=True)
        vidyut.download_data(_DATA_DIR)
    return Chandas(str(_METERS_TSV))


class IntroduceSloka(Timeline):
    sloka: Sloka
    citation: Optional[str]

    def __init__(self, sloka: Sloka, citation: Optional[str] = None):
        super().__init__()
        self.sloka = sloka
        self.citation = citation

    @property
    def gui_color(self) -> str:
        return YELLOW

    def construct(self):
        sloka_g = sloka_group(self.sloka)

        for line in sloka_g:
            self.play(Write(line, duration=4.0))

        # After full write-on, first move glyphs into grid boxes (no color)…
        chandas = _get_chandas()
        sloka_chandas_blank = sloka_group_chandas(self.sloka, chandas, blank=True)
        sloka_chandas = sloka_group_chandas(self.sloka, chandas)
        self.play(LenientTransformMatchingDiff(sloka_g, sloka_chandas_blank, duration=0.6))
        # …then reveal the prosodic colors
        self.play(LenientTransformMatchingDiff(sloka_chandas_blank, sloka_chandas, duration=0.6))
        self.play(Wait(2.0))

        if self.citation is not None and self.citation != "sloka":
            citation_text = TypstText(
                set_font(typst_code(self.citation, Language.SANSKRIT), INTRO_FONT),
                scale=SCALE,
            )
            print(citation_text.text)
            citation_text.points.next_to(sloka_chandas, DOWN)
            for animation in [
                Write(citation_text, duration=1.0),
                Wait(1.0),
                FadeOut(Group(sloka_chandas, citation_text)),
            ]:
                self.play(animation)
        else:
            self.play(FadeOut(sloka_chandas))
