import nirukta.patches  # pyright: ignore[reportUnusedImport]

import importlib

from janim.imports import Config, Timeline

from nirukta.nirukta import Nirukta
from nirukta.util import choose_nirukta_file

importlib.reload(nirukta)

chosen = choose_nirukta_file()


class EntryPoint(Timeline):
    CONFIG = Config(fps=24, preview_fps=24)

    def construct(self):
        timeline = Nirukta(chosen).build().to_item().show()
        self.forward_to(timeline.end)
