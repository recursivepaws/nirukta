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
from nirukta.constants import SANSKRIT_FONT, LATIN_FONT, SCALE
from nirukta.models import Language, Sloka
from janim.imports import WHITE

from nirukta.render import set_font, transform_text, typst_code
from typing import List

from nirukta.typst import add_linebreaks, arrange_vertical, box_cell, arrange_horizontal


""" def sloka_group(sloka: Sloka) -> Group[TypstText]:
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
                set_font(sanskritcode, SANSKRIT_FONT),
                scale=SCALE,
            )
        )

    group = Group(*group)
    group.points.arrange(DOWN)
    return group
"""


def sloka_group_english(sloka: Sloka) -> TypstText:
    rows = []

    for line in sloka.lines:
        english = ""
        for vAkya in line.vAkyAni:
            english += vAkya.english + "#linebreak()"

        rows.append(typst_code(english, Language.ENGLISH))

    # grid = arrange_vertical(rows, gutter=0.6)
    grid = add_linebreaks(rows)

    return TypstText(
        set_font(grid, LATIN_FONT),
        scale=SCALE,
    )


def sloka_group_reformed(sloka: Sloka, devanagari: bool) -> TypstText:
    rows = []

    if devanagari:
        lang = Language.SANSKRIT
        font = SANSKRIT_FONT
    else:
        lang = Language.TRANSLIT
        font = LATIN_FONT

    for li, line in enumerate(sloka.lines):
        sanskritcode = ""
        for vi, vAkya in enumerate(line.vAkyAni):
            utterancetext = ""
            for token in vAkya.tokens:
                if isinstance(token, str):
                    utterancetext += token
                else:
                    utterancetext += token.slp1

                utterancetext += " "
            utterance_code = (
                f"{typst_code(utterancetext, lang)}<line_{li}_utterance_{vi}>"
            )
            sanskritcode += utterance_code + " "

        # rows.append(f"[{sanskritcode}]")
        rows.append(sanskritcode)

    # grid = arrange_vertical(rows, gutter=0.6)
    grid = add_linebreaks(rows)

    return TypstText(
        set_font(grid, font),
        scale=SCALE,
    )


@dataclass
class Keyed:
    text: TypstText
    keys: Group


def sloka_group_chandas(
    sloka: Sloka,
    blank: bool = False,
    matras: bool = False,
    devanagari: bool = True,
) -> Keyed:
    if devanagari:
        lang = Language.SANSKRIT
        font = SANSKRIT_FONT
    else:
        lang = Language.TRANSLIT
        font = LATIN_FONT

    all_cells = []
    cell_idx = 0

    (meter_label, padas) = sloka.meter()

    for pada in padas:
        for akshara in pada:
            deva = transform_text(akshara.text, lang)
            fill = None if blank else akshara.rgb_color()
            all_cells.append(
                box_cell(
                    content=deva,
                    wide=matras and akshara.is_long(),
                    idx=cell_idx,
                    fill=fill,
                )
            )
            cell_idx += 1

    rows = []
    row_labels = []

    i = 0
    for idx, pada in enumerate(padas):
        n = len(pada)
        row_cells = all_cells[i : i + n]
        rows.append(arrange_horizontal(row_cells, idx))
        i += n
        row_label = f"row_{idx}"
        row_labels.append(row_label)

    grid_code = arrange_vertical(rows)
    # grid_code = add_linebreaks(rows)
    grid = TypstText(set_font(grid_code, font), scale=SCALE)

    if blank:
        return Keyed(text=grid, keys=Group())

    t = title_and_pada_labels(meter_label, grid, row_labels)
    return Keyed(text=grid, keys=t)


def title_and_pada_labels(
    meter_label: str, texttttt: TypstText, labels: List[str]
) -> Group:
    # Position title and labels relative to the centered grid
    meter_deva = transform_text(meter_label, Language.SANSKRIT)
    title = TypstText(
        set_font(f"#text(fill: white, size: 1.2em)[{meter_deva}]", SANSKRIT_FONT),
        scale=SCALE,
    )
    title.points.next_to(texttttt, UP)
    pada_labels = [transform_text(str(n), Language.SANSKRIT) for n in range(1, 5)]
    labelz = []
    for pada_idx, c_label in enumerate(labels):
        label_text = pada_labels[pada_idx] if pada_idx < len(pada_labels) else ""
        label = TypstText(
            set_font(f"#text(fill: white, size: 0.85em)[{label_text}]", SANSKRIT_FONT),
            scale=SCALE,
        )
        label.points.next_to(texttttt.get_label(c_label), LEFT)
        labelz.append(label)

    return Group(title, *labelz)


""" def sloka_thumbnail(sloka: Sloka) -> Group:
    sloka_text = sloka_group_reformed(sloka, devanagari=True)
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

        group = Group(sloka_text, sloka_border, number_label)
    else:
        sloka_border = SurroundingRect(sloka_text, color=WHITE, buff=MED_SMALL_BUFF)
        group = Group(sloka_text, sloka_border)

    group.points.to_border(UL, buff=MED_SMALL_BUFF)
    return group """
