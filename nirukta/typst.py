from typing import List, Optional


cell_width = 1.6
gutter = 0.2


def box_cell(
    content: str,
    width: Optional[float] = cell_width,
    idx: Optional[int] = None,
    fill: Optional[str] = None,
) -> str:
    # Fallback to blank
    if fill is None:
        fill = "rgb(0, 0, 0, 0)"

    return (
        f"[#box(fill: {fill}, width: {width}em, height: {cell_width}em, radius: 0.4em)"
        f"[#align(center + horizon)[#text(fill: white)[{content}]]]"
        f"{'' if idx is None else f'<cell_{idx}>'}]"
    )


def arrange_horizontal(
    cells: List[str],
    # columns: int,
    idx: Optional[int] = None,
) -> str:
    return (
        f"[#box"
        f"[#grid(columns: (auto,) * {len(cells)}, gutter: {gutter}em, {', '.join(cells)})]"
        f"{'' if idx is None else f'<row_{idx}>'}]"
    )


def arrange_vertical(cells: List[str], gutter: float = gutter) -> str:
    return (
        f"#grid(rows: (auto,) * {len(cells)}, gutter: {gutter}em, {', '.join(cells)})"
    )
