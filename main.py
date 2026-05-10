import os
import sys
import nirukta.patches  # pyright: ignore[reportUnusedImport]  # noqa: F401

from janim.imports import RED, Timeline
from janim.imports import Config

# Rebuild everything in the framework
if os.environ.get("REBUILD"):
    for key in list(sys.modules):
        if key.startswith("nirukta"):
            del sys.modules[key]

from nirukta.util import choose_nirukta_file, is_nirukta_file, file_to_timeline  # noqa: E402

chosen = choose_nirukta_file()


# During `janim run` (preview), render at half resolution to reduce GPU load.
# `janim write` (export) keeps full 1920×1080.
_preview_mode = "run" in sys.argv

class Nirukta(Timeline):
    CONFIG = Config(
        fps=60,
        preview_fps=30,
        pixel_width=960 if _preview_mode else 1920,
        pixel_height=540 if _preview_mode else 1080,
        anti_alias_width=0.001 if _preview_mode else 0.015,
    )

    nirukta: Timeline

    @property
    def gui_color(self) -> str:
        return RED

    def construct(self):
        assert is_nirukta_file(chosen), "Invalid file"
        timeline = file_to_timeline(chosen).build().to_item().show()
        self.forward_to(timeline.end)
