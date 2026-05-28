from dataclasses import dataclass

from janim.imports import (
    ORANGE,
    Timeline,
)
from nirukta.models import Sloka
from nirukta.timelines.english import EnglishTimeline
from nirukta.timelines.quadrants import QuadrantsTimeline
from nirukta.timelines.recitation import RecitationTimeline


@dataclass
class IntroduceQuadTimeline(Timeline):
    slokas: Sloka

    def __init__(self, sloka: Sloka):
        super().__init__()
        self.sloka = sloka

    @property
    def gui_name(self) -> str:
        return "IntroduceQuad"

    @property
    def gui_color(self) -> str:
        return ORANGE

    def construct(self):
        quadrants = (
            QuadrantsTimeline(
                [
                    RecitationTimeline(self.sloka, devanagari=True, chandas=False),
                    RecitationTimeline(self.sloka, devanagari=False, chandas=False),
                    RecitationTimeline(self.sloka, devanagari=True, chandas=True),
                    EnglishTimeline(self.sloka),
                ]
            )
            .build()
            .to_item()
            .show()
        )
        self.forward(quadrants.duration)
