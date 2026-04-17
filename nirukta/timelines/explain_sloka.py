from typing import List

from janim.imports import YELLOW, Aligned, FadeIn, FadeOut, Succession, Timeline, Write
from nirukta.models import Line, Sloka
from nirukta.render import Awaken, Sleep, sloka_group, sloka_thumbnail
from nirukta.timelines import LenientTransformMatchingDiff, UtteranceTimeline
from nirukta.timelines.line import LineTimeline


class ExplainSloka(Timeline):
    sloka: Sloka

    def __init__(self, sloka: Sloka):
        super().__init__()
        self.sloka = sloka

    @property
    def gui_color(self) -> str:
        return YELLOW

    def construct(self):
        thumbnail = sloka_thumbnail(self.sloka)
        # initial = sloka_group(self.sloka)
        # self.play(Write(initial), duration=0.33)
        # self.play(LenientTransformMatchingDiff(initial, thumbnail[0]), duration=0.33)
        # self.play(Aligned(FadeIn(thumbnail[1:]), Sleep(thumbnail[0])))
        self.play(Aligned(FadeIn(thumbnail), Sleep(thumbnail[0])))

        for li, line in enumerate(self.sloka.lines):
            for vi, vAkya in enumerate(line.vAkyAni):
                if li != 0 or vi != 0:
                    self.play(Sleep(thumbnail[0]))

                selection = thumbnail[0][li].get_label(
                    f"line_{li}_utterance_{vi}"
                )
                self.play(Awaken(selection))

                vt = UtteranceTimeline(vAkya).build().to_item().show()
                self.forward_to(vt.end)


        self.play(Sleep(thumbnail[0]))
        self.play(FadeOut(thumbnail))
