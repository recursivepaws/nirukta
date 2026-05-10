import hashlib
import pickle
from typing import Any, List

from janim.imports import YELLOW, Aligned, FadeIn, FadeOut, Succession, Timeline, Write
from janim.logger import log
from nirukta.models import Line, Sloka
from nirukta.render import Awaken, Sleep, sloka_group, sloka_thumbnail
from nirukta.timelines import (
    LenientTransformMatchingDiff,
    UtteranceTimeline,
    build_utterance_cached,
)
from nirukta.timelines.line import LineTimeline

# Keyed by MD5 of pickled utterance data.
# Persists across JAnim GUI rebuilds so unchanged utterances are never re-built.
_built_cache: dict[str, Any] = {}


def build_explain_sloka_cached(sloka: Sloka):
    """Return a cached BuiltTimeline for *vAkya*, building it only on first use."""
    key = hashlib.md5(pickle.dumps((sloka.lines, sloka.number))).hexdigest()
    if key not in _built_cache:
        _built_cache[key] = ExplainSloka(sloka).build()

    log.info(f"Reusing sloka build: {sloka.number}")
    return _built_cache[key]


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

                selection = thumbnail[0][li].get_label(f"line_{li}_utterance_{vi}")
                self.play(Awaken(selection))

                vt = build_utterance_cached(vAkya).to_item().show()
                self.forward_to(vt.end)

        self.play(Sleep(thumbnail[0]))
        self.play(FadeOut(thumbnail))
