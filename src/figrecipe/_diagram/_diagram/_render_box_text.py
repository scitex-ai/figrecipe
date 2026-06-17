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


def _build_text_items(
    box: "BoxSpec", title_color, colors: Dict
) -> List[Tuple[str, float, str, object]]:
    """Build the ordered (text, fontsize, fontweight, color) list for a box.

    Title first, optional subtitle, then each content line (dict or str) with
    the bullet prefix applied.
    """
    is_code = box.shape == "codeblock"
    items: List[Tuple[str, float, str, object]] = [(box.title, 11, "bold", title_color)]
    if box.subtitle:
        items.append((box.subtitle, 9, "normal", colors["text"]))
    bullet_prefixes = {"circle": "· ", "dash": "– ", "arrow": "→ "}
    for line in box.content:
        pfx = bullet_prefixes.get(box.bullet, "")
        if isinstance(line, dict):
            items.append(
                (
                    pfx + line.get("text", ""),
                    line.get("fontsize", 8),
                    line.get("fontweight", "normal"),
                    line.get("color", colors["text"]),
                )
            )
        else:
            items.append(
                (pfx + str(line), 8 if not is_code else 7, "normal", colors["text"])
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
    """Draw a box's title / subtitle / content as vertically stacked rows."""
    is_code = box.shape == "codeblock"
    items = _build_text_items(box, title_color, colors)

    # Text area = PositionSpec minus padding on all sides
    inner_h = pos.height_mm - 2 * box.padding_mm
    n = len(items)
    gap = min(inner_h / max(n, 1) * 0.85, 6.0) if n > 1 else 0
    block_h = gap * (n - 1)
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
    for i, (text, fsize, fweight, fcolor) in enumerate(items):
        ax.text(
            x_text,
            top_y - i * gap,
            text,
            ha=ha,
            va="center",
            fontsize=fsize,
            fontweight=fweight,
            color=fcolor,
            fontfamily="monospace" if is_code and i > 0 else "sans-serif",
            fontstyle="normal",
            zorder=7,
            bbox=txt_bg,
        )


# EOF
