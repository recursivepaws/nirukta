"""Export the final (fully-deconstructed) state of every utterance to a PDF.

A table: each verse line in Devanagari on the left, that line's utterances as
outlined boxes on the right (each showing the coloured Devanagari + IAST + English
final state). Thin rules separate lines; bolder rules separate slokas. Black
background to match the JAnim style.

Run like validate.py:  uv run typst_output.py
(or non-interactively:  NIRUKTA_FILE=library/birthday.sloka uv run typst_output.py)
"""

import os
import tempfile

import typst

from nirukta.util import choose_nirukta_file, is_nirukta_file
from nirukta.parsing.visitors.sloka import SlokaVisitor
from nirukta.parsing.visitors.sutra import SutraVisitor
from nirukta.timelines.utterance import utterance_final_typst
from nirukta.render import transform_text
from nirukta.models import Language
from nirukta.constants import SANSKRIT_FONT, LATIN_FONT

BOLD_RULE = "table.hline(stroke: 1.6pt + white)"
THIN_RULE = "table.hline(stroke: 0.4pt + gray)"


def _utterance_box(utterance) -> str:
    """An outlined box with the utterance's final-state Devanagari / IAST / English."""
    try:
        deva, iast, english = utterance_final_typst(utterance)
    except Exception as e:  # incomplete annotations etc. — don't sink the whole PDF
        print(f"  ! skipped utterance {utterance.english!r}: {e}")
        deva = transform_text(utterance.slp1(), Language.SANSKRIT)
        iast = english = ""
    return (
        "[#rect(stroke: 0.5pt + white, radius: 4pt, inset: 8pt)[\n"
        f'  #text(font: "{SANSKRIT_FONT}", size: 1em)[{deva}]\\\n'
        f'  #text(font: "{LATIN_FONT}", size: 1em)[{iast}]\\\n'
        f'  #text(font: "{LATIN_FONT}", size: 1em)[{english}]\n'
        "]]"
    )


def _line_cells(line) -> tuple[str, str]:
    """(left Devanagari cell, right row-of-boxes cell) for one verse line."""
    deva = transform_text(line.slp1(), Language.SANSKRIT)
    left = f'[#text(font: "{SANSKRIT_FONT}", size: 1em)[{deva}]]'

    boxes = ",\n".join(_utterance_box(v) for v in line.vAkyAni)
    right = f"[#grid(columns: (auto,) * {len(line.vAkyAni)}, column-gutter: 1em, align: top,\n{boxes}\n)]"
    return left, right


def build_document(slokas) -> str:
    rows: list[str] = []
    for sloka in slokas:
        rows.append(BOLD_RULE)  # bolder rule between slokas
        for li, line in enumerate(sloka.lines):
            if li > 0:
                rows.append(THIN_RULE)  # thin rule between lines
            left, right = _line_cells(line)
            rows.append(f"{left}, {right}")
    rows.append(BOLD_RULE)  # bottom

    body = ",\n".join(rows)
    return (
        '#set page(fill: rgb("000000"), margin: 1.5em, flipped: true)\n'
        "#set text(fill: white, size: 1.1em)\n\n"
        "#table(\n"
        "  columns: (auto, 1fr),\n"
        "  stroke: none,\n"
        "  align: horizon + left,\n"
        "  row-gutter: 1em,\n"
        "  column-gutter: 1.2em,\n"
        f"{body}\n"
        ")\n"
    )


def main() -> None:
    chosen = choose_nirukta_file()
    assert is_nirukta_file(chosen), "Invalid file"

    if ".sutra" in chosen:
        slokas = SutraVisitor(chosen).parse().slokas
    else:
        slokas = [SlokaVisitor(chosen).parse().sloka]

    document = build_document(slokas)

    out = os.path.splitext(os.path.basename(chosen))[0] + ".pdf"
    with tempfile.NamedTemporaryFile(
        "w", suffix=".typ", dir=".", delete=False, encoding="utf-8"
    ) as f:
        f.write(document)
        typ_path = f.name
    try:
        typst.compile(typ_path, output=out, font_paths=["fonts"])
    finally:
        os.remove(typ_path)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
