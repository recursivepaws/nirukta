from janim.imports import ORANGE, Timeline
from nirukta.models import Sloka, SlokaFile
from nirukta.timelines.explain_sloka import ExplainSloka
from nirukta.timelines.introduce_sloka import IntroduceSloka


class SlokaFileTimeline(Timeline):
    citation: str
    sloka: Sloka

    def __init__(self, file: SlokaFile):
        super().__init__()
        self.citation = file.citation
        self.sloka = file.sloka

    @property
    def gui_name(self) -> str:
        return self.citation

    @property
    def gui_color(self) -> str:
        return ORANGE

    def construct(self):
        introduction = (
            IntroduceSloka(self.sloka, self.citation).build().to_item().show()
        )
        self.forward(introduction.duration)

        # quadrants = (
        #     IntroduceQuadTimeline(self.sloka, first=True, last=True)
        #     .build()
        #     .to_item()
        #     .show()
        # )
        # self.forward(quadrants.duration)

        explanation = ExplainSloka(self.sloka).build().to_item().show()
        self.forward(explanation.duration)
