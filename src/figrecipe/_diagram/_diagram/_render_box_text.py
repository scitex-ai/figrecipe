#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Text layout for diagram boxes.

Extracted from ``_render.py`` (which sits at the 512-line file limit) so the
box-text vertical stacking can be maintained on its own. ``render_box`` in
``_render.py`` is now a thin orchestrator that draws the box shape and then
delegates the title / subtitle / content text to :func:`render_box_text`.

The vertical budget mirrors :meth:`Diagram._auto_box_height` in ``_core.py``:
a box reserves vertical space for its title, optional subtitle and each content
line.
"""

from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ._core import BoxSpec, PositionSpec

# Max pitch between consecutive text rows (mm); keeps tall boxes from spreading
# their lines too far apart while still letting short boxes breathe.
_MAX_ROW_GAP_MM = 6.0
# Fraction of the per-row slot used as the row pitch, so rows do not butt right
# up against the box padding.
_ROW_FILL = 0.85


def _build_text_items(
    box: "BoxSpec", title_color, colors: Dict
) -> List[Tuple[str, float, str, object]]:
    """Build the ordered (text, fontsize, fontweight, color) list for a box.

    Title first, optional subtitle, then each content line (dict or str) with
    the bullet prefix applied.

    Font sizes come from the active figrecipe style (the same source regular
    figures read). A box title IS the node's label, so it uses ``node_size``
    (axis_label_pt); the subtitle and content lines are secondary detail and
    use the smaller ``edge_label_size`` (legend_pt), preserving the original
    intra-box hierarchy (title > subtitle ~= content). Codeblock content keeps
    its dedicated 7pt monospace size (verbatim code, not a label) and explicit
    per-line ``fontsize`` dict overrides are honoured.
    """
    from .._shared._styles_native import resolve_font_config

    font = resolve_font_config()
    is_code = box.shape == "codeblock"
    items: List[Tuple[str, float, str, object]] = [
        (box.title, font["node_size"], "bold", title_color)
    ]
    if box.subtitle:
        items.append((box.subtitle, font["edge_label_size"], "normal", colors["text"]))
    bullet_prefixes = {"circle": "· ", "dash": "– ", "arrow": "→ "}
    for line in box.content:
        pfx = bullet_prefixes.get(box.bullet, "")
        if isinstance(line, dict):
            items.append(
                (
                    pfx + line.get("text", ""),
                    line.get("fontsize", font["edge_label_size"]),
                    line.get("fontweight", "normal"),
                    line.get("color", colors["text"]),
                )
            )
        else:
            items.append(
                (
                    pfx + str(line),
                    font["edge_label_size"] if not is_code else 7,
                    "normal",
                    colors["text"],
                )
            )
    return items


def render_box_text(
    ax: "Axes",
    pos: "PositionSpec",
    box: "BoxSpec",
    fill,
    title_color,
    colors: Dict,
) -> None:
    """Draw a box's title / subtitle / content as vertically stacked rows.

    Each item is placed on its own row(s); items whose text contains embedded
    ``\\n`` occupy as many rows as they have visual lines, so a multi-line
    title (e.g. ``"Phase\\nfilterbank"``) no longer renders on top of the
    subtitle or the first content line (NeuroVista Ask 4). Counting items
    instead of visual lines was the bug: matplotlib stacks a multi-line string
    as a block taller than a single row, so the next item's row landed inside
    that block.
    """
    is_code = box.shape == "codeblock"
    items = _build_text_items(box, title_color, colors)

    # Number of *visual* rows: an item with N embedded newlines spans N rows.
    line_counts = [text.count("\n") + 1 for text, _, _, _ in items]
    n_rows = sum(line_counts)

    # Text area = PositionSpec minus padding on all sides; the row pitch packs
    # n_rows evenly into it. A single row has no pitch (centred in the box).
    inner_h = pos.height_mm - 2 * box.padding_mm
    row_gap = (
        min(inner_h / max(n_rows, 1) * _ROW_FILL, _MAX_ROW_GAP_MM) if n_rows > 1 else 0
    )
    block_h = row_gap * (n_rows - 1)
    top_y = pos.y_mm + block_h / 2

    # Only use text background if box has no fill (transparent background)
    # Otherwise text would be double-highlighted with box fill + text bbox fill
    txt_bg = (
        None
        if fill and fill != "none"
        else dict(facecolor="white", edgecolor="none", pad=0.5, alpha=0.85)
    )
    ha = "left" if is_code else "center"
    x_text = (pos.x_mm - pos.width_mm / 2 + box.padding_mm) if is_code else pos.x_mm

    # Walk items top-to-bottom. ``row_cursor`` is the top row index of the
    # current item; a multi-line item is centred on the rows it occupies so its
    # own lines stay tight while consecutive items stay separated.
    row_cursor = 0
    for (text, fsize, fweight, fcolor), n_lines in zip(items, line_counts):
        center_row = row_cursor + (n_lines - 1) / 2
        ax.text(
            x_text,
            top_y - center_row * row_gap,
            text,
            ha=ha,
            va="center",
            fontsize=fsize,
            fontweight=fweight,
            color=fcolor,
            fontfamily="monospace" if is_code and row_cursor > 0 else "sans-serif",
            fontstyle="normal",
            zorder=7,
            bbox=txt_bg,
        )
        row_cursor += n_lines


# EOF
