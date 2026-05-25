from dataclasses import dataclass
from typing import List, Optional

from janim.imports import (
    LEFT,
    MED_SMALL_BUFF,
    ORANGE,
    ORIGIN,
    RIGHT,
    UL,
    DL,
    UP,
    DOWN,
    UR,
    DR,
    WHITE,
    Aligned,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    RectClip,
    ShrinkToEdge,
    Succession,
    SurroundingRect,
    Text,
    Timeline,
    Transform,
    TypstText,
    Wait,
    Write,
)
from nirukta.constants import INACTIVE, SANSKRIT_FONT, SCALE
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
    transform_text,
    set_font,
    typst_code,
)
from nirukta.sloka import (
    sloka_group_chandas,
    sloka_group_english,
    sloka_group_reformed,
    sloka_thumbnail,
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

        # Listening side by side with pronunciation guide
        # for sloka in self.slokas:
        #     sloka.meter()
        # slp1 = sloka.slp1()

        # sloka.
        # verse = MI.identify_meter(slp1)             # from_scheme auto-detected; output IAST
        # print(verse.meter_label)
        # print(verse.summarize())
        # verse = MI.identify_meter(slp1, resplit_option='none')
        # verse = MI.identify_meter(slp1, from_scheme='SLP', resplit_option='resplit_lite')

        listen = "SravaRa"
        # recite = "pAWa"
        # title = TypstText(
        #     set_font(
        #         f"#text(fill: white, size: 1.2em)[{transform_text(listen, Language.SANSKRIT)}]",
        #         SANSKRIT_FONT,
        #     ),
        #     scale=SCALE,
        # )
        # title.points.move_to(UL)
        # self.play(FadeIn(title))

        for sloka in self.slokas:
            # introduction = IntroduceSloka(sloka).build().to_item()

            # left = sloka_group(sloka)
            # right = sloka_group(sloka)
            # left.points.scale(0.5)
            # right.points.scale(0.5)
            # right.points.to_border(UR, buff=MED_SMALL_BUFF)

            scaledown = 0.5

            def place_in_corner(clip, corner):
                # TODO: fiddle w this
                clip.transform.set(scale=scaledown)
                clip.points.scale(scaledown)
                clip.points.to_border(corner, buff=0)

            listen_deva = sloka_group_reformed(sloka, devanagari=True)
            speak_deva = sloka_group_reformed(sloka, devanagari=True)

            listen_iast = sloka_group_reformed(sloka, devanagari=False)
            # speak_iast = sloka_group_reformed(sloka, devanagari=False)

            listen_deva_clip = RectClip(listen_deva, anchor=ORIGIN, border=True)
            speak_deva_clip = RectClip(speak_deva, anchor=ORIGIN, border=True)
            listen_iast_clip = RectClip(listen_iast, anchor=ORIGIN, border=True)
            # speak_iast_clip = RectClip(speak_iast, anchor=ORIGIN, border=True)

            place_in_corner(listen_deva_clip, UL)
            place_in_corner(listen_iast_clip, UR)
            place_in_corner(speak_deva_clip, DOWN)
            # speak_deva.points.scale((2.0, 1.0, 1.0))
            speak_deva_clip.points.scale((2.0, 1.0, 1.0))

            iiiii = SurroundingRect(speak_deva, buff=0)
            # place_in_corner(speak_iast_clip, DR)

            listen_deva.points.shift(DOWN * 6)
            listen_deva.points.scale(0.5)
            listen_iast.points.shift(DOWN * 6)
            listen_iast.points.scale(0.5)

            self.play(
                Succession(
                    Aligned(
                        Aligned(
                            listen_deva.anim.points.scale(2.0),
                            listen_deva.anim.points.shift(UP * 6),
                            listen_iast.anim.points.scale(2.0),
                            listen_iast.anim.points.shift(UP * 6),
                        ),
                        FadeIn(
                            Group(
                                iiiii,
                                listen_deva,
                                listen_deva_clip,
                                listen_iast,
                                listen_iast_clip,
                                speak_deva,
                                speak_deva_clip,
                                # speak_iast,
                                # speak_iast_clip,
                            )
                        ),
                    ),
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

            blank_deva = sloka_group_chandas(
                sloka, blank=True, matras=False, devanagari=True
            )
            chandas_deva = sloka_group_chandas(
                sloka, blank=False, matras=False, devanagari=True
            )
            # blank_iast = sloka_group_chandas(
            #     sloka, blank=True, matras=False, devanagari=False
            # )
            # chandas_iast = sloka_group_chandas(
            #     sloka, blank=False, matras=False, devanagari=False
            # )

            speak_deva_clip.apply(
                iiiii,
                blank_deva.text,
                blank_deva.keys,
                chandas_deva.text,
                chandas_deva.keys,
            )
            # speak_iast_clip.apply(
            #     blank_iast.text, blank_iast.keys, chandas_iast.text, chandas_iast.keys
            # )

            self.play(
                Aligned(
                    LenientTransformMatchingDiff(speak_deva, blank_deva.text),
                    # LenientTransformMatchingDiff(speak_iast, blank_iast.text),
                )
            )
            self.play(
                Aligned(
                    Transform(blank_deva.text, chandas_deva.text),
                    # Transform(blank_iast.text, chandas_iast.text),
                )
            )
            self.play(Wait(1.0))
            self.play(
                FadeIn(
                    Group(
                        chandas_deva.keys,
                        # chandas_iast.keys
                    )
                )
            )
            self.prepare(
                Aligned(
                    Aligned(
                        listen_deva.anim.points.scale(0.5),
                        listen_deva.anim.points.shift(UP * 6),
                        listen_iast.anim.points.scale(0.5),
                        listen_iast.anim.points.shift(UP * 6),
                    ),
                    FadeOut(
                        Group(
                            listen_deva_clip,
                            listen_iast_clip,
                            chandas_deva.keys,
                            chandas_deva.text,
                            # chandas_iast.keys,
                            # chandas_iast.text,
                            speak_deva_clip,
                            iiiii,
                            # speak_iast_clip,
                        )
                    ),
                ),
                duration=1.0,
            )

        # self.play(FadeOut(title))

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
