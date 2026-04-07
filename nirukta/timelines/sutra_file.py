from dataclasses import dataclass
from typing import List, Optional

from janim.imports import (
    DOWN,
    GREY,
    MED_SMALL_BUFF,
    ORANGE,
    ORIGIN,
    RIGHT,
    UL,
    WHITE,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Indicate,
    Succession,
    SurroundingRect,
    Timeline,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import INTRO_FONT, SCALE
from nirukta.models import Language, Sloka, SutraFile
from nirukta.timelines import UtteranceTimeline
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
            group = Group()
            sloka_text: Optional[Group[TypstText]] = None
            numbered = False

            if sloka.number is not None:
                number_text = TypstText(
                    text_box(f"{sloka.number}", WHITE),
                    scale=SCALE,
                )
                number_text.points.to_border(UL, buff=MED_SMALL_BUFF)

                number_border = SurroundingRect(
                    number_text,
                    color=WHITE,
                )
                number_border.round_corners(0.5)

                sloka_text = sloka_group(sloka)
                sloka_text.points.scale(0.6)
                sloka_text.points.next_to(number_text, RIGHT / 2.0 + DOWN / 2.0)
                sloka_text.anim.set(color=GREY)
                sloka_border = SurroundingRect(
                    Group(sloka_text, number_border), color=WHITE, buff=MED_SMALL_BUFF
                )
                sloka_border.apply_style(stroke_radius=0.01)

                group.add(number_text, number_border, sloka_text, sloka_border)

                print(f"SLOKA NUMBER: {sloka.number}")
                numbered = True
                # group.add(number_text)
                # group.add(number_border)

            # sloka_border.round_corners(0.25)

            # group = Group(sloka_text, sloka_border)

            def grey_anim(sloka_text: Group[TypstText]):
                return Aligned(
                    *(line.anim.set(color=GREY) for line in sloka_text), duration=1.0
                )

            if numbered and sloka_text is not None:
                self.play(Aligned(FadeIn(group), grey_anim(sloka_text)))

            for li, line in enumerate(sloka.lines):
                # animation = LineTimeline(line).build().to_item().show()

                for vi, vAkya in enumerate(line.vAkyAni):
                    if sloka_text is not None:
                        if li != 0 or vi != 0:
                            self.play(grey_anim(sloka_text))

                        selection = sloka_text[li].get_label(
                            f"line_{li}_utterance_{vi}"
                        )
                        self.play(
                            Succession(
                                Indicate(selection, color=WHITE),
                                selection.anim.set(color=WHITE),
                                lag_ratio=0.4,
                                duration=0.5,
                            ),
                        )

                    vt = UtteranceTimeline(vAkya).build().to_item().show()
                    self.forward_to(vt.end)

                    # if sloka_text is not None:
                    #     self.play(selection.anim.set(color=WHITE), duration=1.0)

                # self.forward_to(animation.end)

            if numbered:
                self.play(FadeOut(group))
