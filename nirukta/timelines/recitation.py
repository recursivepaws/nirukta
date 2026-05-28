from dataclasses import dataclass
import sys

from janim.imports import (
    Aligned,
    Config,
    FadeIn,
    FadeOut,
    Group,
    Succession,
    Timeline,
    Transform,
    Wait,
)
from nirukta.models import Sloka
from nirukta.sloka import sloka_group_chandas, sloka_group_reformed
from nirukta.timelines import LenientTransformMatchingDiff


@dataclass
class RecitationTimeline(Timeline):
    sloka: Sloka
    devanagari: bool
    chandas: bool

    def __init__(self, sloka: Sloka, devanagari: bool, chandas: bool):
        super().__init__()
        self.sloka = sloka
        self.devanagari = devanagari
        self.chandas = chandas

    def construct(self):
        if self.chandas:
            c = sloka_group_chandas(self.sloka, blank=False, matras=False)
            group = Group(c.text, c.keys)
        else:
            group = sloka_group_reformed(self.sloka, devanagari=self.devanagari)

        self.play(
            Succession(
                FadeIn(group),
                Wait(1.0),
            )
        )
        self.play(Succession(Wait(2.0), FadeOut(group, duration=0.5)))

        """ if self.chandas:
            blank = sloka_group_chandas(self.sloka, blank=True, matras=False)
            chandas = sloka_group_chandas(self.sloka, blank=False, matras=False)

            self.play(
                Succession(
                    LenientTransformMatchingDiff(group, blank.text, duration=0.5),
                    Aligned(
                        Transform(blank.text, chandas.text),
                        FadeIn(chandas.keys),
                        duration=0.5,
                    ),
                    Wait(1.0),
                    FadeOut(
                        Group(
                            chandas.keys,
                            chandas.text,
                        ),
                        duration=0.5,
                    ),
                )
            )
        else:
            self.play(Succession(Wait(2.0), FadeOut(group, duration=0.5))) """
