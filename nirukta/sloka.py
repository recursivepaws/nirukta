from attr import dataclass
from janim.imports import (
    BLUE_E,
    RED_E,
    LEFT,
    MED_SMALL_BUFF,
    UL,
    AnimGroup,
    Rect,
    DOWN,
    UP,
    Group,
    SurroundingRect,
    Text,
    TypstText,
)
from nirukta.constants import INTRO_FONT, LATIN_FONT, SCALE
from nirukta.models import Language, Sloka
from janim.imports import WHITE

from nirukta.render import scale_with_stroke, set_font, transform_text, typst_code
from nirukta.chandas import chandas
from typing import Tuple, List

_LONG_VOWELS_SLP1 = frozenset("AIUFXeEoO")


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
                set_font(sanskritcode, INTRO_FONT),
                scale=SCALE,
            )
        )

    group = Group(*group)
    group.points.arrange(DOWN)
    return group


def _is_long_vowel(slp1: str) -> bool:
    """True if the SLP1 akshara contains a long vowel (dīrgha = 2 mātrās)."""
    return any(c in _LONG_VOWELS_SLP1 for c in slp1)


@dataclass
class Keyed:
    text: TypstText
    keys: Group


def sloka_group_chandas(
    sloka: Sloka,
    blank: bool = False,
    matras: bool = False,
) -> Keyed:
    base_width = 1.8
    gutter = 0.5

    all_cells = []
    cell_idx = 0
    cell_labels = []
    for line in sloka.lines:
        for vAkya in line.vAkyAni:
            for token in vAkya.tokens:
                if isinstance(token, str):
                    continue
                match = chandas.classify(token.slp1)
                for pada in match.aksharas:
                    for akshara in pada:
                        bg = BLUE_E if akshara.weight == "G" else RED_E
                        deva = transform_text(akshara.text, Language.SANSKRIT)
                        fill = (
                            "rgb(0, 0, 0, 0)" if blank else f'rgb("{bg.lstrip("#")}")'
                        )
                        width = (
                            f"{base_width * 2}em"
                            if (matras and _is_long_vowel(akshara.text))
                            else f"{base_width}em"
                        )
                        cell_label = f"cell_{cell_idx}"
                        all_cells.append(
                            f"[#box(fill: {fill}, width: {width}, height: {base_width}em, radius: 0.4em)"
                            f"[#align(center + horizon)[#text(fill: white)[{deva}]]]"
                            f" <{cell_label}>]"
                        )
                        cell_labels.append(cell_label)
                        cell_idx += 1

    pada_size = 8

    rows = []
    row_labels = []
    for i in range(0, len(all_cells), pada_size):
        row_cells = all_cells[i : i + pada_size]
        n = len(row_cells)
        row_label = f"row_{i}"
        rows.append(
            f"[#box[#grid(columns: (auto,) * {n}, gutter: {gutter}em, {', '.join(row_cells)})] <{row_label}>]"
        )
        row_labels.append(row_label)

    grid_code = f"#grid(rows: (auto,) * {n}, gutter: {gutter}em, {', '.join(rows)})"
    grid = TypstText(set_font(grid_code, INTRO_FONT), scale=SCALE)

    if blank:
        return Keyed(text=grid, keys=Group())

    t = title_and_pada_labels(grid, row_labels)
    return Keyed(text=grid, keys=t)


def title_and_pada_labels(texttttt: TypstText, labels: List[str]) -> Group:
    # Position title and labels relative to the centered grid
    meter_deva = transform_text("anuzwuB", Language.SANSKRIT)
    title = TypstText(
        set_font(f"#text(fill: white, size: 1.4em)[{meter_deva}]", INTRO_FONT),
        scale=SCALE,
    )
    title.points.next_to(texttttt, UP)
    pada_labels = [transform_text(str(n), Language.SANSKRIT) for n in range(1, 5)]
    labelz = []
    for pada_idx, c_label in enumerate(labels):
        label_text = pada_labels[pada_idx] if pada_idx < len(pada_labels) else ""
        label = TypstText(
            set_font(f"#text(fill: white, size: 0.85em)[{label_text}]", INTRO_FONT),
            scale=SCALE,
        )
        label.points.next_to(texttttt.get_label(c_label), LEFT)
        labelz.append(label)

    return Group(title, *labelz)


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
