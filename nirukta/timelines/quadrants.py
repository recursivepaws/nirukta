from dataclasses import dataclass
from typing import List

from janim.imports import (
    BLUE,
    Config,
    WHITE,
    FadeIn,
    FadeOut,
    Group,
    Rect,
    Timeline,
    TransformableFrameClip,
)


@dataclass
class QuadrantsTimeline(Timeline):
    timelines: List[Timeline]
    scale: float

    def __init__(self, timelines: List[Timeline], scale: float = 0.5):
        # Exit early if args are invalid
        if len(timelines) > 4 or len(timelines) < 1:
            raise ValueError(f"Cannot display ${len(timelines)} in a quadrant layout.")

        super().__init__()
        self.timelines = timelines
        self.scale = scale

    @property
    def gui_name(self) -> str:
        return "Quadrants"

    @property
    def gui_color(self) -> str:
        return BLUE

    def construct(self):
        fw = Config.get.frame_width
        fh = Config.get.frame_height
        quad_w = fw / 2
        quad_h = fh / 2

        borders = []
        for i in range(4):
            col = i % 2
            row = i // 2
            center = (
                (col + 0.5 - 1.0) * quad_w,
                (1.0 - row - 0.5) * quad_h,
                0,
            )

            border = Rect(quad_w, quad_h, color=WHITE, stroke_radius=0.03)
            border.points.move_to(center)
            borders.append(border)
        self.play(FadeIn(Group(*borders)))

        # for sloka in self.timelines:
        offsets = [(-0.25, +0.25), (+0.25, +0.25), (-0.25, -0.25), (+0.25, -0.25)]
        durations = []

        for idx, timeline in enumerate(self.timelines):
            built_timeline = timeline.build().to_item().show()
            TransformableFrameClip(
                built_timeline, offset=offsets[idx], scale=self.scale
            ).show()
            durations.append(built_timeline.duration)

        # Wait
        self.forward(max(durations))

        self.play(FadeOut(Group(*borders)))
