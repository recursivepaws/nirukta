from dataclasses import dataclass
from typing import List

from janim.imports import (
    ORANGE,
    ORIGIN,
    SMALL_BUFF,
    UL,
    UR,
    WHITE,
    FadeIn,
    FadeOut,
    Group,
    SurroundingRect,
    Timeline,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import INTRO_FONT, SCALE
from nirukta.models import Language, Sloka, SutraFile
from nirukta.timelines.line import LineTimeline
from nirukta.render import set_font, text_box, typst_code, sloka_group


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
            set_font(typst_code(self.citation, Language.SANSKRIT), INTRO_FONT),
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
            sloka_text = sloka_group(sloka)
            sloka_text.points.scale(0.6)
            sloka_text.points.to_border(UL, buff=SMALL_BUFF)
            sloka_border = SurroundingRect(sloka_text, color=WHITE)
            sloka_border.apply_style(stroke_radius=0.01)
            # sloka_border.round_corners(0.25)

            group = Group(sloka_text, sloka_border)

            if sloka.number is not None:
                print(f"SLOKA NUMBER: {sloka.number}")
                number_text = TypstText(
                    text_box(f"{sloka.number}", WHITE),
                    scale=SCALE,
                )
                number_text.points.to_border(UR, buff=SMALL_BUFF)

                number_border = SurroundingRect(
                    number_text,
                    color=WHITE,
                )
                number_border.round_corners(0.25)
                group.add(number_text)
                group.add(number_border)

            self.play(FadeIn(group))

            # sloka.bui
            for line in sloka.lines:
                animation = LineTimeline(line).build().to_item().show()
                self.forward_to(animation.end)

            self.play(FadeOut(group))
