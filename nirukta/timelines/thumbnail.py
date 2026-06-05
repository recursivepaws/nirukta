import hashlib
import dill as pickle
from typing import Any, List

from janim.imports import (
    LEFT,
    MED_SMALL_BUFF,
    UL,
    UR,
    UP,
    WHITE,
    YELLOW,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    Succession,
    SurroundingRect,
    Text,
    Timeline,
    Write,
)
from janim.logger import log
from nirukta.models import Line, Sloka
from nirukta.render import Awaken, Sleep
from nirukta.sloka import sloka_group_reformed
from nirukta.timelines import (
    LenientTransformMatchingDiff,
    UtteranceTimeline,
    build_utterance_cached,
)
from nirukta.timelines.line import LineTimeline

# Memory-only cache: disk caching is handled at the utterance level.
_built_cache: dict[str, Any] = {}


class ThumbnailTimeline(Timeline):
    sloka: Sloka
    devanagari: bool

    def __init__(self, sloka: Sloka, devanagari: bool):
        super().__init__()
        self.sloka = sloka
        self.devanagari = devanagari

    @property
    def gui_color(self) -> str:
        return YELLOW

    def construct(self):
        # thumbnail = sloka_thumbnail(self.sloka)

        sloka_text = sloka_group_reformed(self.sloka, devanagari=self.devanagari)
        if self.sloka.number is not None:
            number_label = Group(
                Rect(0.4, 0.4, fill_alpha=0.3),
                Text(f"{self.sloka.number}", font_size=22),
            )
            number_label.points.next_to(
                sloka_text, UP, buff=MED_SMALL_BUFF, aligned_edge=LEFT
            )
            sloka_border = SurroundingRect(
                Group(sloka_text, number_label), color=WHITE, buff=MED_SMALL_BUFF
            )

            group = Group(sloka_text, sloka_border, number_label)
        else:
            sloka_border = SurroundingRect(sloka_text, color=WHITE, buff=MED_SMALL_BUFF)
            group = Group(sloka_text, sloka_border)

        group.points.to_border(UL if self.devanagari else UR, buff=MED_SMALL_BUFF)
        # return group
        # initial = sloka_group(self.sloka)
        # self.play(Write(initial), duration=0.33)
        # self.play(LenientTransformMatchingDiff(initial, thumbnail[0]), duration=0.33)
        # self.play(Aligned(FadeIn(thumbnail[1:]), Sleep(thumbnail[0])))

        self.play(Aligned(FadeIn(group), Sleep(sloka_text)))

        print()
        print(sloka_text.text)
        print()

        for li, line in enumerate(self.sloka.lines):
            for vi, vAkya in enumerate(line.vAkyAni):
                if li != 0 or vi != 0:
                    self.play(Sleep(group))

                selection = sloka_text.get_label(f"line_{li}_utterance_{vi}")
                self.play(Awaken(selection))

                # Build but do not show; so that we can match durations
                # vt = build_utterance_cached(vAkya).to_item()
                vt = UtteranceTimeline(vAkya).build().to_item()
                self.forward(vt.duration)

        self.play(Sleep(sloka_text))
        self.play(FadeOut(group))
