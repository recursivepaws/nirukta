from dataclasses import dataclass
from typing import List, Optional

from janim.imports import (
    LEFT,
    MED_SMALL_BUFF,
    ORANGE,
    ORIGIN,
    UL,
    UP,
    WHITE,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    SurroundingRect,
    Text,
    Timeline,
    Transform,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import INACTIVE, INTRO_FONT, SCALE
from nirukta.models import Language, Sloka, SutraFile
from nirukta.timelines import LenientTransformMatchingDiff, UtteranceTimeline
from nirukta.render import (
    Awaken,
    Sleep,
    scale_with_stroke,
    set_font,
    sloka_group_english,
    sloka_thumbnail,
    typst_code,
    sloka_group,
)
from nirukta.timelines.explain_sloka import ExplainSloka


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
            explain = ExplainSloka(sloka).build().to_item().show()
            self.forward_to(explain.end)

            # thumbnail = sloka_thumbnail(sloka)
            # initial = sloka_group(sloka)
            # self.play(Write(initial), duration=0.33)
            # self.play(LenientTransformMatchingDiff(initial, thumbnail[0]), duration=0.33)
            # self.play(Aligned(FadeIn(thumbnail[1:]), Sleep(thumbnail[0])))
            #
            # for li, line in enumerate(sloka.lines):
            #     for vi, vAkya in enumerate(line.vAkyAni):
            #         if li != 0 or vi != 0:
            #             self.play(Sleep(thumbnail[0]))
            #
            #         selection = thumbnail[0][li].get_label(
            #             f"line_{li}_utterance_{vi}"
            #         )
            #         self.play(Awaken(selection))
            #
            #         vt = UtteranceTimeline(vAkya).build().to_item().show()
            #         self.forward_to(vt.end)
            #
            # self.play(FadeOut(thumbnail))

