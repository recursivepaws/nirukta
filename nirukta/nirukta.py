from __future__ import annotations
from janim.imports import RED, Timeline
from nirukta.util import is_nirukta_file, file_to_timeline


class Nirukta(Timeline):
    nirukta: Timeline

    @property
    def gui_color(self) -> str:
        return RED

    def __init__(self, file: str):
        super().__init__()
        assert is_nirukta_file(file), "Invalid file"
        self.nirukta = file_to_timeline(file)

    def construct(self):
        animation = self.nirukta.build().to_item().show()
        self.forward_to(animation.end)
