from typing import Union
from janim.imports import RED, Config, Timeline
from parser import SlokaFile, SutraFile


class Nirukta(Timeline):
    nirukta: Union[SlokaFile, SutraFile]
    CONFIG = Config(fps=24)

    @property
    def gui_color(self) -> str:
        return RED

    def __init__(self, nirukta: Union[SlokaFile, SutraFile]):
        super().__init__()
        self.nirukta = nirukta

    def construct(self):
        animation = self.nirukta.build().to_item().show()
        self.forward_to(animation.end)
