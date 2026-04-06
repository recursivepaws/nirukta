import nirukta.patches  # pyright: ignore[reportUnusedImport]

from janim.imports import RED, Timeline
from nirukta.util import is_nirukta_file, file_to_timeline

import importlib

from janim.imports import Config
from nirukta.util import choose_nirukta_file

importlib.reload(nirukta)

chosen = choose_nirukta_file()


class Nirukta(Timeline):
    CONFIG = Config(fps=60, preview_fps=60)

    nirukta: Timeline

    @property
    def gui_color(self) -> str:
        return RED

    def construct(self):
        assert is_nirukta_file(chosen), "Invalid file"
        timeline = file_to_timeline(chosen).build().to_item().show()
        self.forward_to(timeline.end)
