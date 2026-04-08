from janim.imports import (
    DOWN,
    UP,
    FadeOut,
    Group,
    GrowFromEdge,
    ShrinkToEdge,
    TypstText,
    VItem,
    linear,
    rush_into,
)
from nirukta.constants import INTRO_FONT, SCALE, TYPST_CMD_RE
from nirukta.models import Language, Sloka
from janim.imports import WHITE
from aksharamukha import transliterate

from dataclasses import dataclass, field
from typing import Optional
from nirukta.models import Animation


@dataclass
class Diff:
    anim: Animation
    token_id: Optional[str] = field(default=None)

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
                return 0.55
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
            sanskritcode += utterance_code

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
    return f'#set text(font: "{font}", stroke: none)\n#set page(width: {240 * SCALE}pt)\n{text}'


def text_box(text: str, color: str):
    if color == "#FFFFFF":
        return f"#box[#text[{text}]]"
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


def typst_code(text: str, language: Language, color: str = WHITE):
    transformed = transform_text(text, language)
    return text_box(transformed, color)


def scale_with_stroke(group: Group, factor: float) -> Group:
    group.points.scale(factor)
    for item in group.walk_descendants(VItem):
        item.radius.set(item.radius.get() * factor)
    return group
