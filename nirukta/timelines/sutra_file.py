from dataclasses import dataclass
from typing import List

from janim.imports import (
    ORANGE,
    ORIGIN,
    FadeOut,
    Succession,
    Timeline,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import SANSKRIT_FONT
from nirukta.models import Language, Sloka, SutraFile
from nirukta.render import (
    set_font,
    typst_code,
)
from nirukta.timelines import ExplainSloka
from nirukta.timelines.introduce_quad import IntroduceQuadTimeline


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
        if self.citation != "unknown":
            citation = TypstText(
                set_font(typst_code(self.citation, Language.SANSKRIT), SANSKRIT_FONT),
            )
            citation.points.move_to(ORIGIN)

            # Introduce the text by its title
            self.play(
                Succession(
                    Write(citation),
                    Wait(1.5),
                    FadeOut(citation),
                )
            )

        for idx, sloka in enumerate(self.slokas):
            quadrants = (
                IntroduceQuadTimeline(
                    sloka, first=(idx == 0), last=(idx == len(self.slokas) - 1)
                )
                .build()
                .to_item()
                .show()
            )
            self.forward(quadrants.duration)

        # for sloka in self.slokas:
        #     introduce = IntroduceSloka(sloka=sloka).build().to_item().show()
        #     self.forward(introduce.duration)

        for sloka in self.slokas:
            explain = ExplainSloka(sloka=sloka).build().to_item().show()
            self.forward(explain.duration)
