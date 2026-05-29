from janim.imports import (
    C_LABEL_ANIM_DEFAULT,
    C_LABEL_ANIM_OUT,
    Aligned,
    Cmpt_Rgbas,
    DataUpdater,
    RateFunc,
    SupportsAnim,
    AnimGroup,
    Succession,
    DOWN,
    UP,
    FadeOut,
    Group,
    GrowFromEdge,
    ShrinkToEdge,
    ValueTracker,
    double_smooth,
    linear,
    rush_into,
    smooth,
)
from nirukta.constants import INACTIVE, TYPST_CMD_RE
from nirukta.models import Language
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
            return double_smooth

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


def set_font(text: str, font: str, ratio: float = 1.0, wrap: bool = False):
    ratio *= 1.3
    result = f'#set text(font: "{font}", size: {ratio}em, stroke: none)\n'
    if wrap:
        result += f"#set page(width: {266 * ratio}pt)\n"

    result += f"{text}"
    return result


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


def untransform_text(text: str):
    if text == "":
        return ""
    iast = transliterate.process("DEVANAGARI", "IAST", text)
    if not iast:
        raise ValueError(f'Cannot represent "{text}" in IAST')
    return iast


def typst_code(
    text: str, language: Language, color: str = WHITE, stroke_mode: bool = False
):
    transformed = transform_text(text, language)
    return text_box(transformed, color, stroke_mode)


# def scale_with_stroke(group: Group, factor: float) -> Group:
#     group.points.scale(factor)
#     for item in group.walk_descendants(VItem):
#         item.radius.set(item.radius.get() * factor)
#     return group
