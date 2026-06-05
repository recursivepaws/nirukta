from typing import Optional

from janim.anims.transform import Transform
from janim.imports import (
    FadeIn,
    DOWN,
    YELLOW,
    FadeOut,
    Group,
    Timeline,
    TypstText,
    Wait,
    Write,
    Aligned,
)

from nirukta.constants import SANSKRIT_FONT, SCALE
from nirukta.models import Language, Sloka
from nirukta.render import (
    set_font,
    typst_code,
)
from nirukta.sloka import (
    sloka_group_chandas,
    sloka_group_reformed,
    sloka_group_overview,
)
from nirukta.timelines.transform import LenientTransformMatchingDiff


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
        sloka_g = sloka_group_overview(self.sloka, devanagari=True)

        # for line in sloka_g:
        self.play(Write(sloka_g, duration=4.0))

        self.play(Wait(1.0))

        # Move glyphs into grid boxes
        sloka_chandas_blank = sloka_group_chandas(self.sloka, blank=True)
        sloka_chandas = sloka_group_chandas(self.sloka)
        #
        self.play(
            LenientTransformMatchingDiff(
                sloka_g, sloka_chandas_blank.text, duration=0.5
            )
        )
        self.play(Wait(1.0))
        #
        # Reveal the prosodic colors
        self.play(Transform(sloka_chandas_blank.text, sloka_chandas.text, duration=0.6))
        self.play(Wait(1.0))
        # Reveal keys
        self.play(FadeIn(sloka_chandas.keys))

        self.play(Wait(2.0))

        self.play(FadeOut(sloka_chandas.keys))

        self.play(Transform(sloka_chandas.text, sloka_chandas_blank.text, duration=0.6))

        self.play(
            LenientTransformMatchingDiff(
                sloka_chandas_blank.text, sloka_g, duration=0.5
            )
        )

        self.play(Wait(2.0))

        if self.citation is not None and self.citation != "sloka":
            citation_text = TypstText(
                set_font(typst_code(self.citation, Language.SANSKRIT), SANSKRIT_FONT),
            )
            print(citation_text.text)
            citation_text.points.next_to(sloka_g, DOWN)
            for animation in [
                Write(citation_text, duration=1.0),
                Wait(1.0),
                FadeOut(Group(sloka_g, citation_text)),
            ]:
                self.play(animation)
        else:
            self.play(FadeOut(sloka_g))
