from dataclasses import dataclass
from typing import List

from janim.imports import (
    Config,
    ORANGE,
    ORIGIN,
    WHITE,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    Timeline,
    TransformableFrameClip,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import SANSKRIT_FONT, SCALE
from nirukta.models import Language, Sloka, SutraFile
from nirukta.render import (
    set_font,
    typst_code,
)
from nirukta.timelines.english import EnglishTimeline
from nirukta.timelines.quadrants import QuadrantsTimeline
from nirukta.timelines.recitation import RecitationTimeline


@dataclass
class SutraFileTimeline(Timeline):
    citation: str
    slokas: List[Sloka]

    def __init__(self, file: SutraFile):
        super().__init__()
        self.citation = file.citation
        self.slokas = file.slokas

    @property
    def gui_name(self) -> str:
        return self.citation

    @property
    def gui_color(self) -> str:
        return ORANGE

    def construct(self):
        citation = TypstText(
            set_font(typst_code(self.citation, Language.SANSKRIT), SANSKRIT_FONT),
            scale=SCALE,
        )
        citation.points.move_to(ORIGIN)

        # Introduce the text by its title
        for animation in [
            Write(citation),
            Wait(1.5),
            FadeOut(citation),
        ]:
            self.play(animation)

        for sloka in self.slokas:
            quadrants = (
                QuadrantsTimeline(
                    [
                        RecitationTimeline(sloka=sloka, devanagari=True, chandas=False),
                        RecitationTimeline(
                            sloka=sloka, devanagari=False, chandas=False
                        ),
                        RecitationTimeline(sloka=sloka, devanagari=True, chandas=True),
                        EnglishTimeline(sloka=sloka),
                    ]
                )
                .build()
                .to_item()
                .show()
            )
            self.forward(quadrants.duration)
