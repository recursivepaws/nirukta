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


vertical = os.environ.get("NIRUKTA_VERTICAL") == "1"
preview_mode = "run" in sys.argv

if preview_mode:
    config = Config(
        fps=60,
        preview_fps=30,
        pixel_width=540 if vertical else 960,
        pixel_height=960 if vertical else 540,
        frame_width=8.0 if vertical else 16.0 / 9.0 * 8.0,
        frame_height=16.0 / 9.0 * 8.0 if vertical else 8.0,
        anti_alias_width=0.001,
    )
else:
    config = Config(
        fps=60,
        pixel_width=1080 if vertical else 1920,
        pixel_height=1920 if vertical else 1080,
        frame_width=8.0 if vertical else 16.0 / 9.0 * 8.0,
        frame_height=16.0 / 9.0 * 8.0 if vertical else 8.0,
    )


class Nirukta(Timeline):
    CONFIG = config
    __rebuildable_name__ = "Nirukta"

    @property
    def gui_color(self) -> str:
        return RED

    def construct(self):
        chosen = choose_nirukta_file()
        assert is_nirukta_file(chosen), "Invalid file"
        stem = os.path.splitext(os.path.basename(chosen))[0]
        sloka_idx = os.environ.get("NIRUKTA_SLOKA_INDEX")
        if sloka_idx is not None:
            stem = f"{stem}-sloka-{int(sloka_idx) + 1}"
        suffix = "vertical" if vertical else "horizontal"
        type(self).__name__ = f"{stem}-{suffix}"
        timeline = file_to_timeline(chosen).build().to_item().show()
        self.forward(timeline.duration)
