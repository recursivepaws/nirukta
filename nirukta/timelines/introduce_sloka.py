from typing import Optional
from janim.imports import DOWN, YELLOW, FadeOut, Group, Timeline, TypstText, Wait, Write
from nirukta.models import Language, Sloka
from nirukta.render import sloka_group, set_font, typst_code
from nirukta.constants import INTRO_FONT, SCALE


class IntroduceSloka(Timeline):
    sloka: Sloka
    citation: Optional[str]

    def __init__(self, sloka: Sloka, citation: Optional[str] = None):
        super().__init__()
        self.sloka = sloka
        self.citation = citation

    @property
    def gui_color(self) -> str:
        return YELLOW

    def construct(self):
        sloka_g = sloka_group(self.sloka)

        for line in sloka_g:
            self.play(Write(line, duration=4.0))

        if self.citation is not None and self.citation != "sloka":
            citation_text = TypstText(
                set_font(typst_code(self.citation, Language.SANSKRIT), INTRO_FONT),
                scale=SCALE,
            )
            print(citation_text.text)
            citation_text.points.next_to(sloka_g, DOWN)
            for animation in [
                Wait(2.0),
                Write(citation_text, duration=1.0),
                Wait(1.0),
                FadeOut(Group(sloka_g, citation_text)),
            ]:
                self.play(animation)
        else:
            self.play(Wait(1.0))
            self.play(FadeOut(sloka_g))
