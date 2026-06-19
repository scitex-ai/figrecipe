#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendering functions for diagram diagrams."""

from typing import TYPE_CHECKING, Dict

from matplotlib.axes import Axes
from matplotlib.patches import (
    FancyArrowPatch,
    FancyBboxPatch,
)

from ..._utils._units import mm_to_pt
from .._shared._styles_native import COLORS as _COLORS
from .._shared._styles_native import (
    get_edge_style,
    get_emphasis_style,
    resolve_font_config,
)

if TYPE_CHECKING:
    from ._core import ArrowSpec, BoxSpec, Diagram


def _render_cylinder(ax, pos, fill, border, zorder=2):
    """Draw a database cylinder shape (rectangle body + top/bottom ellipses)."""
    from matplotlib.patches import Ellipse, Rectangle

    x = pos.x_mm - pos.width_mm / 2
    y = pos.y_mm - pos.height_mm / 2
    w = pos.width_mm
    h = pos.height_mm
    ry = min(h * 0.18, w * 0.15)  # ellipse half-height

    # Body rectangle (between ellipse centers)
    body = Rectangle(
        (x, y + ry), w, h - 2 * ry, facecolor=fill, edgecolor="none", zorder=zorder
    )
    ax.add_patch(body)

    # Left and right edges of body
    ax.plot(
        [x, x], [y + ry, y + h - ry], color=border, linewidth=2, zorder=zorder + 0.1
    )
    ax.plot(
        [x + w, x + w],
        [y + ry, y + h - ry],
        color=border,
        linewidth=2,
        zorder=zorder + 0.1,
    )

    # Bottom ellipse (front half only — arc)
    bot = Ellipse(
        (x + w / 2, y + ry),
        w,
        2 * ry,
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder + 0.2,
    )
    ax.add_patch(bot)

    # Top ellipse (full, visible)
    top = Ellipse(
        (x + w / 2, y + h - ry),
        w,
        2 * ry,
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder + 0.3,
    )
    ax.add_patch(top)


def _render_codeblock(ax, pos, fill, border, zorder=2):
    """Draw a code block shape (rounded rectangle with a colored title bar)."""
    x = pos.x_mm - pos.width_mm / 2
    y = pos.y_mm - pos.height_mm / 2
    w = pos.width_mm
    h = pos.height_mm
    bar_h = min(h * 0.18, 4.5)

    # Full rounded box (body + bar as one shape)
    outer = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0,rounding_size=2.0",
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder,
    )
    ax.add_patch(outer)

    # Title bar overlay — plain Rectangle clipped to the outer rounded box
    # so it has rounded top corners but a flat bottom (no seam artifacts)
    from matplotlib.patches import Rectangle

    bar = Rectangle(
        (x, y + h - bar_h),
        w,
        bar_h + 10,
        facecolor=border,
        edgecolor="none",
        zorder=zorder + 0.05,
    )
    bar.set_clip_path(outer)
    ax.add_patch(bar)

    # Window dots (three small circles in the title bar)
    dot_r = min(bar_h * 0.2, 0.8)
    dot_y = y + h - bar_h / 2
    for i, dot_color in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        dot_x = x + 2.5 + i * (dot_r * 3)
        ax.plot(
            dot_x,
            dot_y,
            "o",
            color=dot_color,
            markersize=max(dot_r * 1.5, 2),
            zorder=zorder + 0.2,
            markeredgewidth=0,
        )


def _render_document(ax, pos, fill, border, zorder=2):
    """Draw a document/paper shape (rectangle with folded top-right corner)."""
    from matplotlib.patches import Polygon

    x = pos.x_mm - pos.width_mm / 2
    y = pos.y_mm - pos.height_mm / 2
    w = pos.width_mm
    h = pos.height_mm
    fold = min(w * 0.15, h * 0.2, 5.0)

    # Main body (pentagon — top-right corner cut)
    body = Polygon(
        [
            (x, y),
            (x + w, y),
            (x + w, y + h - fold),
            (x + w - fold, y + h),
            (x, y + h),
        ],
        closed=True,
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder,
    )
    ax.add_patch(body)

    # Fold triangle (dog-ear)
    fold_tri = Polygon(
        [
            (x + w - fold, y + h),
            (x + w - fold, y + h - fold),
            (x + w, y + h - fold),
        ],
        closed=True,
        facecolor=border,
        edgecolor=border,
        linewidth=1,
        alpha=0.3,
        zorder=zorder + 0.1,
    )
    ax.add_patch(fold_tri)


def _render_file(ax, pos, fill, border, zorder=2):
    """Draw a file/folder shape (rectangle with tab on top-left)."""
    from matplotlib.patches import Polygon, Rectangle

    x = pos.x_mm - pos.width_mm / 2
    y = pos.y_mm - pos.height_mm / 2
    w = pos.width_mm
    h = pos.height_mm
    tab_w = w * 0.35
    tab_h = min(h * 0.15, 3.0)

    # Main body
    body = Rectangle(
        (x, y),
        w,
        h - tab_h,
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder,
    )
    ax.add_patch(body)

    # Tab on top-left
    tab = Polygon(
        [
            (x, y + h - tab_h),
            (x + tab_w, y + h - tab_h),
            (x + tab_w + tab_h, y + h),
            (x, y + h),
        ],
        closed=True,
        facecolor=fill,
        edgecolor=border,
        linewidth=2,
        zorder=zorder + 0.1,
    )
    ax.add_patch(tab)


# Aesthetic pad for FancyBboxPatch rounding (does NOT affect layout) - now 1mm
_AESTHETIC_PAD = 1.0


def render_container(diagram: "Diagram", ax: Axes, cid: str, container: Dict) -> None:
    """Render a container box."""
    pos = diagram._positions[cid]
    colors = get_emphasis_style(container["emphasis"])
    fill = container.get("fill_color")
    fill = fill if fill is not None else colors["fill"]
    border = container.get("border_color")
    border = border if border is not None else colors["stroke"]

    box = FancyBboxPatch(
        (pos.x_mm - pos.width_mm / 2, pos.y_mm - pos.height_mm / 2),
        pos.width_mm,
        pos.height_mm,
        boxstyle="round,pad=1.0,rounding_size=3.0",
        facecolor=fill,
        edgecolor=border,
        linewidth=2.5,
        zorder=1,
    )
    ax.add_patch(box)

    if container.get("title"):
        _bg = dict(facecolor="none", edgecolor="none", pad=1.0)
        loc = container.get("title_loc", "upper center")
        _v, _h = (loc.split() + ["center"])[:2]
        hw = pos.width_mm / 2
        hh = pos.height_mm / 2
        ty = pos.y_mm + (hh - 1.5 if _v == "upper" else -hh + 1.5)
        tx = pos.x_mm + (-hw + 3 if _h == "left" else hw - 3 if _h == "right" else 0)
        ha = {"left": "left", "right": "right"}.get(_h, "center")
        va = "top" if _v == "upper" else "bottom"
        ax.text(
            tx,
            ty,
            container["title"],
            ha=ha,
            va=va,
            fontsize=resolve_font_config()["title_size"],
            fontweight="bold",
            color=colors["text"],
            zorder=7,
            bbox=_bg,
        )

    diagram._render_info[cid] = {"pos": pos}


def render_box(diagram: "Diagram", ax: Axes, bid: str, box: "BoxSpec") -> None:
    """Render a rich text box."""
    pos = diagram._positions[bid]
    colors = get_emphasis_style(box.emphasis)
    fill = box.fill_color or colors["fill"]
    border = box.border_color or colors["stroke"]
    title_color = box.title_color or colors["text"]
    pad = _AESTHETIC_PAD

    # Codeblock with language: override colors from Emacs theme unless explicit
    if box.shape == "codeblock" and box.language and not box.fill_color:
        from ._codeblock import _find_default_theme, parse_emacs_theme

        theme_path = _find_default_theme()
        if theme_path:
            faces = parse_emacs_theme(theme_path)
            fill = faces.get("_bg", fill)
            if not box.border_color:
                border = faces.get("_bg_dark", border)

    if box.shape == "cylinder":
        _render_cylinder(ax, pos, fill, border)
    elif box.shape == "codeblock":
        _render_codeblock(ax, pos, fill, border)
    elif box.shape == "document":
        _render_document(ax, pos, fill, border)
    elif box.shape == "file":
        _render_file(ax, pos, fill, border)
    else:
        shape_styles = {
            "box": f"square,pad={pad}",
            "rounded": f"round,pad={pad},rounding_size=2.0",
            "stadium": f"round,pad={pad},rounding_size=5.0",
        }
        boxstyle = shape_styles.get(box.shape, shape_styles["rounded"])

        patch = FancyBboxPatch(
            (pos.x_mm - pos.width_mm / 2, pos.y_mm - pos.height_mm / 2),
            pos.width_mm,
            pos.height_mm,
            boxstyle=boxstyle,
            facecolor=fill,
            edgecolor=border,
            linewidth=2,
            zorder=2,
        )
        ax.add_patch(patch)

    # Codeblock with syntax highlighting gets special text rendering
    if box.shape == "codeblock" and box.content and box.language:
        from ._codeblock import render_codeblock_text

        render_codeblock_text(ax, pos, box, fill, title_color, colors)
        diagram._render_info[bid] = {"pos": pos}
        return

    # Title / subtitle / content text layout lives in _render_box_text so this
    # file stays under the 512-line limit (see that module for the per-line
    # vertical stacking rules).
    from ._render_box_text import render_box_text

    render_box_text(ax, pos, box, fill, title_color, colors)

    diagram._render_info[bid] = {"pos": pos}


def render_icon(diagram, ax, iid, icon):
    """Delegate to icons module."""
    from ._icons import render_icon as _ri

    _ri(diagram, ax, iid, icon)


def render_arrow(diagram: "Diagram", ax: Axes, arrow: "ArrowSpec") -> None:
    """Render an arrow."""
    if arrow.source not in diagram._positions or arrow.target not in diagram._positions:
        return

    src_pos = diagram._positions[arrow.source]
    tgt_pos = diagram._positions[arrow.target]

    # Determine anchors
    if arrow.source_anchor == "auto" or arrow.target_anchor == "auto":
        auto_src, auto_tgt = diagram._auto_anchor(src_pos, tgt_pos)
        src_anc = auto_src if arrow.source_anchor == "auto" else arrow.source_anchor
        tgt_anc = auto_tgt if arrow.target_anchor == "auto" else arrow.target_anchor
    else:
        src_anc, tgt_anc = arrow.source_anchor, arrow.target_anchor

    start = diagram._get_anchor(src_pos, src_anc)
    end = diagram._get_anchor(tgt_pos, tgt_anc)

    import math

    _DEFAULT_CLEARANCE = 1.0
    dx, dy = end[0] - start[0], end[1] - start[1]
    dist = math.hypot(dx, dy)
    if dist > 1e-6:
        ux, uy = dx / dist, dy / dist
        clearance = (
            arrow.margin_mm if arrow.margin_mm is not None else _DEFAULT_CLEARANCE
        )
        total_perp = clearance + _AESTHETIC_PAD

        def _margin_for_anchor(anc):
            if anc in ("top-left", "top-right", "bottom-left", "bottom-right"):
                return total_perp * math.sqrt(2)
            elif anc in ("top", "bottom"):
                return total_perp / abs(uy) if abs(uy) > 1e-6 else total_perp
            elif anc in ("left", "right"):
                return total_perp / abs(ux) if abs(ux) > 1e-6 else total_perp
            return total_perp

        margin = max(_margin_for_anchor(src_anc), _margin_for_anchor(tgt_anc))
        margin = min(margin, dist * 0.25)
        if dist > margin * 2:
            start = (start[0] + ux * margin, start[1] + uy * margin)
            end = (end[0] - ux * margin, end[1] - uy * margin)
    start = (start[0] + arrow.source_dx, start[1] + arrow.source_dy)
    end = (end[0] + arrow.target_dx, end[1] + arrow.target_dy)
    style = get_edge_style(arrow.style)
    color = _COLORS.get(arrow.color, arrow.color) if arrow.color else style["color"]
    conn = f"arc3,rad={arrow.curve}" if arrow.curve else "arc3,rad=0"
    linewidth_pt = mm_to_pt(arrow.linewidth_mm)

    patch = FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle="-|>",
        color=color,
        linestyle=style["linestyle"],
        linewidth=linewidth_pt,
        connectionstyle=conn,
        mutation_scale=15,
        zorder=5,
    )
    ax.add_patch(patch)

    if arrow.label:
        from ._validate import compute_arrow_label_position

        lx, ly = compute_arrow_label_position(
            start, end, arrow.curve, arrow.label_offset_mm
        )
        _label_bg = dict(facecolor="white", edgecolor="none", pad=1.0, alpha=0.85)
        ax.text(
            lx,
            ly,
            arrow.label,
            ha="center",
            va="center",
            fontsize=resolve_font_config()["edge_label_size"],
            color=color,
            fontstyle="italic",
            zorder=6,
            bbox=_label_bg,
        )


def draw_all_elements(diagram, ax):
    """Draw all diagram elements onto axes (used by Diagram.render)."""
    ax.clear()
    ax.set_xlim(diagram.xlim)
    ax.set_ylim(diagram.ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    for cid in sorted(
        (c for c in diagram._containers if c in diagram._positions),
        key=lambda c: -(
            diagram._positions[c].width_mm * diagram._positions[c].height_mm
        ),
    ):
        render_container(diagram, ax, cid, diagram._containers[cid])
    for bid, box in diagram._boxes.items():
        if bid in diagram._positions:
            render_box(diagram, ax, bid, box)
    for arrow in diagram._arrows:
        render_arrow(diagram, ax, arrow)
    for iid, icon in diagram._icons.items():
        if iid in diagram._positions:
            render_icon(diagram, ax, iid, icon)
    if diagram.title:
        ps = list(diagram._positions.values())
        cx = (
            (
                min(p.x_mm - p.width_mm / 2 for p in ps)
                + max(p.x_mm + p.width_mm / 2 for p in ps)
            )
            / 2
            if ps
            else (diagram.xlim[0] + diagram.xlim[1]) / 2
        )
        ax.text(
            cx,
            diagram.ylim[1] - 5.0,
            diagram.title,
            ha="center",
            va="top",
            fontsize=resolve_font_config()["title_size"],
            fontweight="bold",
        )
