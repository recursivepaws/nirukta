import hashlib
import dill as pickle
from typing import Any

from janim.imports import (
    YELLOW,
    Timeline,
    Wait,
    TransformableFrameClip,
)
from janim.logger import log
from nirukta.models import Sloka
from nirukta.timelines import build_utterance_cached, UtteranceTimeline
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
        # TODO: find a way to run the thumbnail timeline without building the utterances twice
        # utterance_timelines = []
        # timeline_durations = []
        # for li, line in enumerate(self.sloka.lines):
        #     for vi, vAkya in enumerate(line.vAkyAni):
        #         utterance_timelines.append(UtteranceTimeline(vAkya).build())
        # for timeline in utterance_timelines:
        #     timeline_durations.append(timeline.duration)

        scale = 0.7
        thumb = (
            ThumbnailTimeline(sloka=self.sloka, devanagari=True)
            .build()
            .to_item()
            .show()
        )
        TransformableFrameClip(
            thumb,
            offset=(-((1 - scale) / 2), (1 - scale) / 2),
            scale=scale,
        ).show()

        thumb2 = (
            ThumbnailTimeline(sloka=self.sloka, devanagari=False)
            .build()
            .to_item()
            .show()
        )
        TransformableFrameClip(
            thumb2,
            offset=(+((1 - scale) / 2), (1 - scale) / 2),
            scale=scale,
        ).show()

        self.play(Wait(1.0))

        for li, line in enumerate(self.sloka.lines):
            for vi, vAkya in enumerate(line.vAkyAni):
                if li != 0 or vi != 0:
                    self.play(Wait(0.33))

                self.play(Wait(0.33))
                # vt = build_utterance_cached(vAkya).to_item().show()
                vt = UtteranceTimeline(vAkya).build().to_item().show()
                self.forward(vt.duration)

        self.forward_to(thumb.end)
