from janim.imports import (
    C_LABEL_ANIM_DEFAULT,
    C_LABEL_ANIM_OUT,
    GREEN,
    LEFT,
    MED_SMALL_BUFF,
    ORANGE,
    RED,
    TEAL,
    UL,
    Aligned,
    Cmpt_Rgbas,
    DataUpdater,
    ItemUpdater,
    RateFunc,
    Rect,
    SupportsAnim,
    AnimGroup,
    Succession,
    Indicate,
    DOWN,
    UP,
    FadeOut,
    Group,
    GrowFromEdge,
    ShrinkToEdge,
    SurroundingRect,
    Text,
    TypstText,
    VItem,
    ValueTracker,
    double_smooth,
    linear,
    rush_into,
    smooth,
    there_and_back,
)
from nirukta.constants import INACTIVE, INTRO_FONT, LATIN_FONT, SCALE, TYPST_CMD_RE
from nirukta.models import Language, Sloka
from janim.imports import WHITE, C_LABEL_ANIM_ABSTRACT
from aksharamukha import transliterate

from dataclasses import dataclass, field
from nirukta.models import Animation


class FlatAligned(Aligned):
    flat_label = True
    label_color = C_LABEL_ANIM_DEFAULT

    def __init__(
        self,
        *anims: SupportsAnim,
        at: float = 0,
        duration: float | None = None,
        rate_func: RateFunc = linear,
        name: str | None = None,
        collapse: bool = False,
        label_color=None,
    ):
        super().__init__(
            *anims,
            at=at,
            duration=duration,
            rate_func=rate_func,
            name=name,
            collapse=collapse,
        )

        if label_color is not None:
            self.label_color = label_color


class Sleep(AnimGroup):
    flat_label = True
    label_color = C_LABEL_ANIM_OUT

    def __init__(self, *anims: SupportsAnim, duration: float = 0.33, **kwargs) -> None:
        group = Group(*anims)
        color_tracker = ValueTracker(0.0)

        def updater(data, _):
            t = color_tracker.current().get_value()
            for cmpt in data.components.values():
                if not isinstance(cmpt, Cmpt_Rgbas):
                    continue
                cmpt.mix(INACTIVE, factor=t)

        super().__init__(
            Aligned(
                color_tracker.anim.set_value(1.0),
                DataUpdater(
                    group,
                    updater,
                    become_at_end=True,
                    root_only=False,
                ),
                rate_func=linear,
                duration=duration,
            )
        )


class Awaken(AnimGroup):
    flat_label = True
    label_color = C_LABEL_ANIM_ABSTRACT

    def __init__(self, *anims: SupportsAnim, duration: float = 0.33, **kwargs) -> None:
        group = Group(*anims)
        scale_tracker = ValueTracker(1.0)
        color_tracker = ValueTracker(0.0)

        def updater(data, _):
            data.points.scale(scale_tracker.current().get_value())

            t = color_tracker.current().get_value()
            for cmpt in data.components.values():
                if not isinstance(cmpt, Cmpt_Rgbas):
                    continue
                cmpt.mix(WHITE, factor=t)

        super().__init__(
            Aligned(
                color_tracker.anim.set_value(1.0),
                Succession(
                    scale_tracker.anim.set_value(1.16), scale_tracker.anim.set_value(1)
                ),
                DataUpdater(
                    group,
                    updater,
                    duration=duration,
                    become_at_end=True,
                    root_only=False,
                ),
                rate_func=smooth,
                duration=duration,
            )
        )


@dataclass
class Diff:
    anim: Animation
    token_id: str
    initial: bool = field(default=False)

    def name(self):
        return str(self.anim.value)

    def rate_func(self):
        if self.anim == Animation.EXPAND:
            return rush_into
        else:
            return linear

    def duration(self):
        match self.anim:
            case Animation.COLORS:
                return 0.33
            case Animation.SWARAS:
                return 0.44
            case Animation.SPELLS:
                return 0.33
            case Animation.EXPAND:
                return 0.55

    def delay(self):
        return self.duration() * 0.15

    def mismatch(self):
        # Swara removals get a special animation for optimal seamlessness
        if self.anim == Animation.SWARAS:
            return (
                lambda item, p, **kwargs: FadeOut(
                    item, at=self.delay(), shift=UP * 0.1, **kwargs
                ),
                lambda item, p, **kwargs: GrowFromEdge(item, DOWN, **kwargs),
            )
        else:
            return (
                lambda item, p, **kwargs: ShrinkToEdge(
                    item, UP, at=self.delay(), **kwargs
                ),
                lambda item, p, **kwargs: GrowFromEdge(item, DOWN, **kwargs),
            )


def sloka_group(sloka: Sloka) -> Group[TypstText]:
    group = []

    for li, line in enumerate(sloka.lines):
        sanskrit = ""
        sanskritcode = ""
        for vi, vAkya in enumerate(line.vAkyAni):
            utterancetext = ""
            for token in vAkya.tokens:
                if isinstance(token, str):
                    sanskrit += token
                    utterancetext += token
                else:
                    sanskrit += token.slp1
                    utterancetext += token.slp1

                sanskrit += " "
                utterancetext += " "
            utterance_code = f"{typst_code(utterancetext, Language.SANSKRIT)}<line_{li}_utterance_{vi}>"
            sanskritcode += utterance_code + " "

        group.append(
            TypstText(
                # set_font(typst_code(sanskrit, Language.SANSKRIT), INTRO_FONT),
                set_font(sanskritcode, INTRO_FONT),
                scale=SCALE,
            )
        )

    group = Group(*group)
    group.points.arrange(DOWN)
    return group


def sloka_group_chandas(sloka: Sloka, chandas) -> Group:
    """Like sloka_group() but each akshara is colored by prosodic weight.

    Guru (heavy) → ORANGE  |  Laghu (light) → TEAL
    Produces an identical layout to sloka_group() so LenientTransformMatchingDiff
    can match glyphs purely as a color change.
    """
    group = []
    for li, line in enumerate(sloka.lines):
        sanskritcode = ""
        for vi, vAkya in enumerate(line.vAkyAni):
            utterance_code = ""
            for token in vAkya.tokens:
                if isinstance(token, str):
                    utterance_code += text_box(token, WHITE)
                else:
                    match = chandas.classify(token.slp1)
                    for pada in match.aksharas:
                        for akshara in pada:
                            color = ORANGE if akshara.weight == "G" else TEAL
                            utterance_code += typst_code(
                                akshara.text, Language.SANSKRIT, color
                            )
                utterance_code += " "
            sanskritcode += f"{utterance_code}<line_{li}_utterance_{vi}> "

        group.append(TypstText(set_font(sanskritcode, INTRO_FONT), scale=SCALE))

    group = Group(*group)
    group.points.arrange(DOWN)
    return group


def sloka_group_english(sloka: Sloka) -> Group[TypstText]:
    group = []

    for li, line in enumerate(sloka.lines):
        english = ""
        for vi, vAkya in enumerate(line.vAkyAni):
            english += vAkya.english + "#linebreak()"

        group.append(
            TypstText(
                set_font(typst_code(english, Language.ENGLISH), LATIN_FONT),
                scale=SCALE,
            )
        )

    group = Group(*group)
    group.points.arrange(DOWN)
    return group


def sloka_thumbnail(sloka: Sloka) -> Group:
    sloka_text = sloka_group(sloka)
    if sloka.number is not None:
        number_label = Group(
            Rect(0.4, 0.4, fill_alpha=0.3),
            Text(f"{sloka.number}", font_size=22),
        )
        number_label.points.next_to(
            sloka_text, UP, buff=MED_SMALL_BUFF, aligned_edge=LEFT
        )
        sloka_border = SurroundingRect(
            Group(sloka_text, number_label), color=WHITE, buff=MED_SMALL_BUFF
        )

        group = scale_with_stroke(Group(sloka_text, sloka_border, number_label), 0.5)
    else:
        sloka_border = SurroundingRect(sloka_text, color=WHITE, buff=MED_SMALL_BUFF)
        group = scale_with_stroke(Group(sloka_text, sloka_border), 0.5)

    group.points.to_border(UL, buff=MED_SMALL_BUFF)
    return group


def Junicode_translit(iast: str, color: str) -> str:
    """Like Junicode() but splits ṃ into m + combining dot for clean animation."""
    if "ṃ" not in iast:
        return text_box(iast, color)

    def T(s):
        return f'#text(fill: rgb("{color}"))[{s}]'

    parts = iast.split("ṃ")
    inner = ""
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            # everything up to and including the m of ṃ
            inner += T(part + "m")
            inner += r"#h(-0.175em)" + T("\u0323") + r"#h(0.175em)"
        else:
            # tail after the last ṃ
            if part:
                inner += T(part)

    return f"#box[{inner}]"


def set_font(text: str, font: str):
    return f'#set text(font: "{font}", stroke: none)\n#set page(width: {266 * SCALE}pt)\n{text}'


def text_box(text: str, color: str, stroke_mode: bool = False):
    if color == "#FFFFFF" and not stroke_mode:
        return f"#box[#text[{text}]]"
    else:
        color = color.lstrip("#")
        if stroke_mode:
            return f'#box[#text(fill: rgb(0, 0, 0, 0), stroke: 0.5pt + rgb("{color}"))[{text}]]'
        else:
            return f'#box[#text(fill: rgb("{color}"))[{text}]]'


def typst_code_safe(text: str, language: Language, color: str = WHITE) -> str:
    """Like typst_code, but splits out any embedded #foo() commands so they
    are never trapped inside a #box[#text[...]]."""
    parts = TYPST_CMD_RE.split(text)  # alternates: plain text, cmd, plain text, ...
    result = ""
    for part in parts:
        if not part:
            continue
        if TYPST_CMD_RE.fullmatch(part):
            result += part  # emit the command bare, e.g. #linebreak()
        else:
            result += typst_code(part, language, color)
    return result


def transform_text(text: str, language: Language):
    match language:
        case Language.ENGLISH:
            return text
        case Language.TRANSLIT:
            iast = transliterate.process("SLP1", "IAST", text)
            if not iast:
                raise ValueError(f'Cannot represent "{text}" in IAST')
            return iast
        case Language.SANSKRIT:
            deva = transliterate.process("SLP1", "DEVANAGARI", text)
            if not deva:
                raise ValueError(f'Cannot represent "{text}" in devanagari')
            return deva


def typst_code(
    text: str, language: Language, color: str = WHITE, stroke_mode: bool = False
):
    transformed = transform_text(text, language)
    return text_box(transformed, color, stroke_mode)


def scale_with_stroke(group: Group, factor: float) -> Group:
    group.points.scale(factor)
    for item in group.walk_descendants(VItem):
        item.radius.set(item.radius.get() * factor)
    return group
