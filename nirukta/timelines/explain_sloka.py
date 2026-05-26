import hashlib
import dill as pickle
from typing import Any, List

from janim.imports import (
    YELLOW,
    Aligned,
    FadeIn,
    FadeOut,
    Succession,
    Timeline,
    Write,
    TransformableFrameClip,
)
from janim.logger import log
from nirukta.models import Line, Sloka
from nirukta.render import Awaken, Sleep
from nirukta.timelines import (
    LenientTransformMatchingDiff,
    UtteranceTimeline,
    build_utterance_cached,
)
from nirukta.timelines.line import LineTimeline
from nirukta.timelines.thumbnail import ThumbnailTimeline

# Memory-only cache: disk caching is handled at the utterance level.
_built_cache: dict[str, Any] = {}


def build_explain_sloka_cached(sloka: Sloka):
    """Return a cached BuiltTimeline for *sloka*, building it only on first use."""
    key = hashlib.md5(pickle.dumps((sloka.lines, sloka.number))).hexdigest()
    if key in _built_cache:
        log.info(f"Reusing from memory: (sloka {sloka.number})")
        return _built_cache[key]
    built = ExplainSloka(sloka).build()
    _built_cache[key] = built
    return built


class ExplainSloka(Timeline):
    sloka: Sloka

    def __init__(self, sloka: Sloka):
        super().__init__()
        self.sloka = sloka

    @property
    def gui_color(self) -> str:
        return YELLOW

    def construct(self):
        thumb = ThumbnailTimeline(sloka=self.sloka).build().to_item().show()

        TransformableFrameClip(
            thumb,
            offset=(-0.25, 0.25),
            scale=0.5,
        ).show()

        self.forward_to(thumb.end)

        # thumbnail = sloka_thumbnail(self.sloka)
        # # initial = sloka_group(self.sloka)
        # # self.play(Write(initial), duration=0.33)
        # # self.play(LenientTransformMatchingDiff(initial, thumbnail[0]), duration=0.33)
        # # self.play(Aligned(FadeIn(thumbnail[1:]), Sleep(thumbnail[0])))
        # self.play(Aligned(FadeIn(thumbnail), Sleep(thumbnail[0])))
        #
        # for li, line in enumerate(self.sloka.lines):
        #     for vi, vAkya in enumerate(line.vAkyAni):
        #         if li != 0 or vi != 0:
        #             self.play(Sleep(thumbnail[0]))
        #
        #         selection = thumbnail[0][li].get_label(f"line_{li}_utterance_{vi}")
        #         self.play(Awaken(selection))
        #
        #         vt = build_utterance_cached(vAkya).to_item().show()
        #         self.forward_to(vt.end)
        #
        # self.play(Sleep(thumbnail[0]))
        # self.play(FadeOut(thumbnail))
