import sys
import nirukta.patches  # pyright: ignore[reportUnusedImport]

from janim.imports import RED, Timeline
from janim.imports import Config

for key in list(sys.modules):
    if key.startswith('nirukta'):
        del sys.modules[key]

from nirukta.util import choose_nirukta_file, is_nirukta_file, file_to_timeline

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
