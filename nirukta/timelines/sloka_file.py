from janim.imports import ORANGE, FadeOut, Timeline, Wait, Write
from nirukta.models import Sloka, SlokaFile
from nirukta.render import sloka_group_english
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
        introduction = IntroduceSloka(self.sloka, self.citation).build().to_item()
        introduction.show()
        self.forward_to(introduction.end)

        explanation = ExplainSloka(self.sloka.lines).build().to_item()
        explanation.show()
        self.forward_to(explanation.end)

        sge = sloka_group_english(self.sloka)
        self.play(Write(sge))
        self.play(Wait(2.0))
        self.play(FadeOut(sge))
