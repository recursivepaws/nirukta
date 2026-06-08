# from janim.imports import *

from janim.imports import (
    BLACK,
    RED,
    UP,
    WHITE,
    Axes,
    Config,
    Create,
    Dot,
    Group,
    ItemUpdater,
    Rect,
    Timeline,
    TransformableFrameClip,
    TypstMath,
)
import nirukta.patches  # pyright: ignore[reportUnusedImport]  # noqa: F401

import math


class GraphDemonstration(Timeline):
    def __init__(self, f, x_range, typ_code):
        super().__init__()
        self.f = f
        self.x_range = x_range
        self.typ_code = typ_code

    def construct(self):
        axes = Axes(axis_config=dict(include_numbers=True))
        graph = axes.get_graph(self.f, self.x_range, color=RED, stroke_radius=0.05)

        typ = TypstMath(
            self.typ_code, stroke_color=BLACK, stroke_alpha=1, stroke_background=True
        ).show()
        typ.points.scale(1.6).to_border(UP)

        def dots_updater(p):
            points = graph.current().points
            return Group(
                Dot(points.get_start()),
                Dot(points.get_end()),
                fill_color=BLACK,
                stroke_alpha=1,
            )

        self.forward()
        self.play(Create(axes, lag_ratio=0.05))
        self.play(
            Create(graph),
            ItemUpdater(None, dots_updater),
        )


class MainTimeline(Timeline):
    def construct(self):
        params_list = [
            (lambda x: x**2, (-1, 1.5), "f(x) = x^2"),
            (lambda x: x**3, (-1.5, 1.5), "f(x) = x^3"),
            (lambda x: math.sin(x), (-3, 3), "f(x) = sin(x)"),
            (lambda x: math.atan(x), (-2, 2), "f(x) = tan^(-1) x"),
        ]

        cols, rows = 2, 2
        fw = Config.get.frame_width
        fh = Config.get.frame_height
        quad_w = fw / cols
        quad_h = fh / rows

        # clip 1/4 from each side → each quadrant shows the central 1/2 × 1/2
        clip_h = 0.5 - 1 / (2 * cols)  # 0.25
        clip_v = 0.5 - 1 / (2 * rows)  # 0.25

        for idx, params in enumerate(params_list):
            col = idx % cols
            row = idx // cols

            offset_x = -clip_h + col * (1 / cols)  # -0.25 or +0.25
            offset_y = clip_v - row * (1 / rows)  #  0.25 or -0.25

            tl = (
                GraphDemonstration(*params).build().to_item(keep_last_frame=True).show()
            )
            TransformableFrameClip(
                tl,
                # clip=(clip_h, clip_v, clip_h, clip_v),
                offset=(offset_x, offset_y),
                scale=0.5,
            ).show()

            center = (
                (col + 0.5 - 1.0) * quad_w,
                (1.0 - row - 0.5) * quad_h,
                0,
            )
            border = Rect(quad_w, quad_h, color=WHITE, stroke_radius=0.03)
            border.points.move_to(center)
            border.show()

        self.forward(4)
