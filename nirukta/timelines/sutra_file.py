from dataclasses import dataclass
from typing import List, Optional

from janim.imports import (
    LEFT,
    MED_SMALL_BUFF,
    ORANGE,
    ORIGIN,
    RIGHT,
    UL,
    UP,
    UR,
    WHITE,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    RectClip,
    Succession,
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
from nirukta.timelines import (
    IntroduceSloka,
    LenientTransformMatchingDiff,
    UtteranceTimeline,
)
from nirukta.render import (
    Awaken,
    Sleep,
    scale_with_stroke,
    set_font,
    typst_code,
)
from nirukta.sloka import (
    sloka_group_chandas,
    sloka_group_english,
    sloka_thumbnail,
    sloka_group,
)
from nirukta.timelines.explain_sloka import ExplainSloka, build_explain_sloka_cached


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

        # Listening side by side with pronunciation guide
        for sloka in self.slokas:
            sloka.meter()
            # slp1 = sloka.slp1()

            # sloka.
            # verse = MI.identify_meter(slp1)             # from_scheme auto-detected; output IAST
            # print(verse.meter_label)
            # print(verse.summarize())
            # verse = MI.identify_meter(slp1, resplit_option='none')
            # verse = MI.identify_meter(slp1, from_scheme='SLP', resplit_option='resplit_lite')


        for sloka in self.slokas:
            # introduction = IntroduceSloka(sloka).build().to_item()

            # left = sloka_group(sloka)
            # right = sloka_group(sloka)
            # left.points.scale(0.5)
            # right.points.scale(0.5)
            # left.points.to_border(UL, buff=MED_SMALL_BUFF)
            # right.points.to_border(UR, buff=MED_SMALL_BUFF)

            scaledown = 0.5

            lt = sloka_group(sloka)
            rt = sloka_group(sloka)
            left = RectClip(lt, anchor=ORIGIN, border=False)
            left.points.scale(scaledown)
            left.transform.set(scale=scaledown)
            right = RectClip(rt, anchor=ORIGIN, border=False)
            right.transform.set(scale=scaledown)
            right.points.scale(scaledown)


            self.play(

                Succession(
                FadeIn(Group(lt, left, rt, right)),
                Wait(1.0),
                Aligned(
                    left.anim.points.shift(LEFT * scaledown * 6),
                    right.anim.points.shift(RIGHT * scaledown * 6),
                    # right.anim.points.scale(0.2)
                ),
                Wait(1.0),
                # FadeOut(Group(lt, left, rt, right))
                )
            )

            blank = sloka_group_chandas(sloka, blank=True, matras=False)
            chandas = sloka_group_chandas(sloka, blank=False, matras=False)
            g = Group(blank.text, blank.keys, chandas.text, chandas.keys)
            # g.points.shift(RIGHT * 3)

            right.apply(*g)
            # blank.text.points.scale(0.5)
            # blank.text.points.to_border(UR, buff=MED_SMALL_BUFF)

            self.play(LenientTransformMatchingDiff(rt, blank.text))
            self.play(Transform(blank.text, chandas.text))
            self.play(Wait(1.0))
            self.play(FadeIn(chandas.keys))
            self.play(FadeOut(Group(lt, left, chandas.keys, chandas.text, right)))

    # group.points.scale(factor)
            # scale_with_stroke(left, 0.5)
            # scale_with_stroke(right, 0.5)
            # introduction.show()
            # self.forward_to(introduction.end)

        # for sloka in self.slokas:
        #     # explain = build_explain_sloka_cached(sloka).to_item().show()
        #     explain = ExplainSloka(sloka).build().to_item().show()
        #     self.forward_to(explain.end)

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
