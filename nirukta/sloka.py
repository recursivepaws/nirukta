from attr import dataclass
from janim.imports import (
    LEFT,
    UP,
    Group,
    TypstText,
    Config,
)
from nirukta.constants import SANSKRIT_FONT, LATIN_FONT
from nirukta.models import Language, Sloka

from nirukta.render import set_font, transform_text, typst_code
from typing import List

from nirukta.typst import add_linebreaks, arrange_vertical, box_cell, arrange_horizontal


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
            utterance_code = (
                f"{typst_code(vAkya.slp1(), lang)}<line_{li}_utterance_{vi}>"
            )
            sanskritcode += utterance_code + " "

        # rows.append(f"[{sanskritcode}]")
        rows.append(sanskritcode)

    # grid = arrange_vertical(rows, gutter=0.6)
    grid = add_linebreaks(rows)

    return TypstText(
        set_font(grid, font, 0.7),
    )


def sloka_group_overview(sloka: Sloka, devanagari: bool) -> TypstText:
    rows = []

    if devanagari:
        lang = Language.SANSKRIT
        font = SANSKRIT_FONT
    else:
        lang = Language.TRANSLIT
        font = LATIN_FONT

    for line in sloka.lines:
        sanskritcode = typst_code(line.slp1(), lang)
        # rows.append(f"[{sanskritcode}]")
        rows.append(sanskritcode)

    # grid = arrange_vertical(rows, gutter=0.6)
    grid = add_linebreaks(rows)

    return TypstText(
        set_font(grid, font),
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

    # Actual ratio of text to use
    columns = len(padas[0])
    ratio = min(Config.get.frame_width / columns, 1.0)

    grid = TypstText(set_font(grid_code, font, ratio))

    if blank:
        return Keyed(text=grid, keys=Group())

    t = title_and_pada_labels(meter_label, grid, row_labels, ratio)

    return Keyed(text=grid, keys=t)


def title_and_pada_labels(
    meter_label: str, texttttt: TypstText, labels: List[str], ratio: float
) -> Group:
    # Position title and labels relative to the centered grid
    meter_deva = transform_text(meter_label, Language.SANSKRIT)
    title = TypstText(
        set_font(meter_deva, SANSKRIT_FONT, ratio=ratio * 1.2),
    )
    title.points.next_to(texttttt, UP)
    pada_labels = [transform_text(str(n), Language.SANSKRIT) for n in range(1, 5)]
    labelz = []
    for pada_idx, c_label in enumerate(labels):
        label_text = pada_labels[pada_idx] if pada_idx < len(pada_labels) else ""
        label = TypstText(
            set_font(label_text, SANSKRIT_FONT, ratio=ratio),
        )
        label.points.next_to(texttttt.get_label(c_label), LEFT)
        labelz.append(label)

    return Group(title, *labelz)
