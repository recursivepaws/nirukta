from dataclasses import dataclass

from janim.imports import (
    ORIGIN,
    FadeIn,
    FadeOut,
    Group,
    RectClip,
    Succession,
    Timeline,
    Transform,
    Vect,
    Wait,
)
from nirukta.models import Sloka
from nirukta.sloka import sloka_group_chandas, sloka_group_reformed
from nirukta.timelines import LenientTransformMatchingDiff


scaledown = 0.5


def place_in_corner(clip: RectClip, corner: Vect):
    # TODO: fiddle w this
    clip.transform.set(scale=scaledown * 1.3)
    clip.points.scale(scaledown)
    clip.points.to_border(corner, buff=0)


@dataclass
class RecitationTimeline(Timeline):
    sloka: Sloka
    devanagari: bool
    chandas: bool
    corner: Vect

    def construct(self):
        group = sloka_group_reformed(self.sloka, devanagari=True)
        group_clip = RectClip(group, anchor=ORIGIN, border=True)

        self.play(
            Succession(
                FadeIn(group),
                Wait(1.0),
                # Aligned(
                # left.anim.points.shift(LEFT * scaledown * 6),
                # right.anim.points.shift(RIGHT * scaledown * 6),
                # right.anim.points.scale(0.2)
                # ),
                Wait(1.0),
                # FadeOut(Group(lt, left, rt, right))
            )
        )

        if self.chandas:
            blank = sloka_group_chandas(self.sloka, blank=True, matras=False)
            chandas = sloka_group_chandas(self.sloka, blank=False, matras=False)
            group_clip.apply(blank.text, blank.keys, chandas.text, chandas.keys)

            self.play(
                Succession(
                    LenientTransformMatchingDiff(group, blank.text, duration=0.5),
                    Transform(blank.text, chandas.text, duration=0.5),
                    Wait(1.0),
                    FadeIn(chandas.keys, duration=0.5),
                    FadeOut(
                        Group(
                            group,
                            chandas.keys,
                            chandas.text,
                        ),
                        duration=0.5,
                    ),
                )
            )
        else:
            self.play(
                Succession(Wait(2.5), FadeOut(Group(group, group_clip), duration=0.5))
            )
