from dataclasses import dataclass
from typing import List, Optional

from janim.imports import (
    DOWN,
    GREY_B,
    LEFT,
    MED_SMALL_BUFF,
    ORANGE,
    ORIGIN,
    RIGHT,
    UL,
    UP,
    WHITE,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Indicate,
    Rect,
    Succession,
    SurroundingRect,
    Text,
    Timeline,
    Transform,
    TypstText,
    Wait,
    Write,
    np,
)
from nirukta.constants import INTRO_FONT, SCALE
from nirukta.models import Language, Sloka, SutraFile
from nirukta.timelines import UtteranceTimeline
from nirukta.timelines.line import LineTimeline
from nirukta.render import (
    Awaken,
    scale_with_stroke,
    set_font,
    text_box,
    typst_code,
    sloka_group,
)


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

        group = Group()
        for sloka in self.slokas:
            sloka_text: Optional[Group[TypstText]] = None
            numbered = False

            if sloka.number is not None:
                sloka_text = sloka_group(sloka)
                number_label = Group(
                    Rect(0.4, 0.4, fill_alpha=0.3),
                    Text(f"{sloka.number}", font_size=22),
                )
                number_label.points.next_to(
                    sloka_text, UP, buff=MED_SMALL_BUFF, aligned_edge=LEFT
                )

                sloka_border = SurroundingRect(
                    Group(sloka_text, number_label), color=WHITE, buff=MED_SMALL_BUFF
                )

                group = scale_with_stroke(
                    Group(number_label, sloka_text, sloka_border), 0.5
                )
                group.points.to_border(UL, buff=MED_SMALL_BUFF)

                print(f"SLOKA NUMBER: {sloka.number}")
                numbered = True

            def grey_anim(sloka_text: Group[TypstText]):
                return Aligned(
                    *(line.anim.set(color=GREY_B) for line in sloka_text), duration=1.0
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
                        self.play(Awaken(selection))

                    vt = UtteranceTimeline(vAkya).build().to_item().show()
                    self.forward_to(vt.end)

                    # if sloka_text is not None:
                    #     self.play(selection.anim.set(color=WHITE), duration=1.0)

                # self.forward_to(animation.end)

            if numbered:
                self.play(FadeOut(group))

        # self.play(FadeOut(group))
