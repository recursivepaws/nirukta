import os
import sys

from janim.imports import RED, Timeline
from janim.imports import Config

# Must run before nirukta imports so fresh modules are loaded from disk
if os.environ.get("REBUILD") == "1":
    for key in list(sys.modules):
        if key.startswith("nirukta"):
            del sys.modules[key]

import nirukta.patches  # pyright: ignore[reportUnusedImport]  # noqa: F401, E402
from nirukta.util import choose_nirukta_file, is_nirukta_file, file_to_timeline  # noqa: E402


# Keep previews performant with HD exports
preview_mode = "run" in sys.argv
if preview_mode:
    config = Config(
        fps=60,
        preview_fps=30,
        pixel_width=960,
        pixel_height=540,
        anti_alias_width=0.001,
    )
    config_vertical = Config(
        fps=60,
        preview_fps=30,
        pixel_width=540,
        pixel_height=960,
        frame_width=8.0,
        frame_height=16.0 / 9.0 * 8.0,
        anti_alias_width=0.001,
    )
else:
    config = Config(fps=60)
    config_vertical = Config(
        fps=60,
        pixel_width=1080,
        pixel_height=1920,
        frame_width=8.0,
        frame_height=16.0 / 9.0 * 8.0,
    )


class Nirukta(Timeline):
    CONFIG = config
    nirukta: Timeline

    @property
    def gui_color(self) -> str:
        return RED

    def construct(self):
        chosen = choose_nirukta_file()
        assert is_nirukta_file(chosen), "Invalid file"
        timeline = file_to_timeline(chosen).build().to_item().show()
        self.forward(timeline.duration)


class NiruktaVertical(Timeline):
    CONFIG = config_vertical
    nirukta: Timeline

    @property
    def gui_color(self) -> str:
        return RED

    def construct(self):
        chosen = choose_nirukta_file()
        assert is_nirukta_file(chosen), "Invalid file"
        timeline = file_to_timeline(chosen).build().to_item().show()
        self.forward(timeline.duration)
