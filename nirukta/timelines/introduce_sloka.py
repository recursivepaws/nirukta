from typing import Optional

from janim.anims.transform import Transform
from janim.imports import (
    FadeIn,
    DOWN,
    UP,
    YELLOW,
    FadeOut,
    Group,
    Timeline,
    TypstText,
    Wait,
    Write,
    Aligned,
    LEFT,
)

from nirukta.constants import INTRO_FONT, SCALE
from nirukta.models import Language, Sloka
from nirukta.render import (
    FlatAligned,
    set_font,
    transform_text,
    typst_code,
)
from nirukta.sloka import sloka_group, sloka_group_chandas, title_and_pada_labels
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
        sloka_g = sloka_group(self.sloka)

        for line in sloka_g:
            self.play(Write(line, duration=4.0))

        # Move glyphs into grid boxes
        (sloka_chandas_blank, _) = sloka_group_chandas(self.sloka, blank=True)
        (sloka_chandas, chandas_labels) = sloka_group_chandas(self.sloka)

        self.play(
            LenientTransformMatchingDiff(sloka_g, sloka_chandas_blank, duration=0.6)
        )

        # Reveal the prosodic colors
        self.play(Transform(sloka_chandas_blank, sloka_chandas, duration=0.6))
        self.play(Wait(1.0))
        thing1 = title_and_pada_labels(sloka_chandas, chandas_labels)
        self.play(FadeIn(thing1))

        # Expand boxes by vowel duration
        (sloka_matras, matras_labels) = sloka_group_chandas(self.sloka, matras=True)
        thing2 = title_and_pada_labels(sloka_matras, matras_labels)

        self.play(
            Aligned(
                Transform(sloka_chandas, sloka_matras),
                Transform(thing1, thing2),
                duration=0.8,
            )
        )

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
                FadeOut(Group(sloka_matras, citation_text)),
            ]:
                self.play(animation)
        else:
            self.play(FadeOut(sloka_matras))
