#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-readable layout introspection for composed figures.

The agent-facing FOUNDATION for tight page-packing: given a composed figure (or
just a grid spec), report — as plain structured data — where the panels are,
their mm sizes, and WHERE the blank regions are. Downstream tooling (an agent or
the auto-tiler) consumes this to decide how to resize/re-author panels so the
page is used tightly. Deterministic geometry only (panel bounding boxes), never
pixel inspection — figrecipe layouts are always axis-aligned.

Coordinate conventions (so an agent can reason unambiguously):
- ``*_frac`` are figure-fraction; ``*_mm`` are millimetres on the canvas.
- The ORIGIN for reported boxes is the TOP-LEFT (y grows downward), matching how
  humans describe panels ("bottom-right cell"). matplotlib's native bbox is
  bottom-up; we convert.
"""

from typing import Any, Dict, List, Optional, Tuple

__all__ = ["empty_cells", "layout_report"]


def empty_cells(
    layout: Optional[Tuple[int, int]],
    sources: Dict[Any, Any],
) -> List[Tuple[int, int]]:
    """Blank ``(row, col)`` cells of a GRID compose (deterministic fast path).

    For grid composition (``layout=(nrows, ncols)`` with ``sources`` keyed by
    ``(row, col)``), returns the cells with no source = ``{all cells} -
    set(sources keys)``, sorted row-major. When ``layout`` is omitted it is
    inferred from the max present (row, col). Returns ``[]`` for non-grid
    (tiled/mm) layouts — those are whitespace-free by construction and have no
    grid-cell concept.
    """
    grid_keys = [k for k in sources.keys() if isinstance(k, tuple) and len(k) == 2]
    if layout is None:
        if not grid_keys:
            return []
        nrows = max(k[0] for k in grid_keys) + 1
        ncols = max(k[1] for k in grid_keys) + 1
    elif isinstance(layout, tuple) and len(layout) == 2:
        nrows, ncols = layout
    else:
        return []  # tiled (list-of-rows) / mm layouts have no empty grid cells
    present = set(grid_keys)
    return sorted(
        (r, c) for r in range(nrows) for c in range(ncols) if (r, c) not in present
    )


def _box_panel(
    x0: float, y0: float, x1: float, y1: float, cw: float, ch: float
) -> Dict:
    """Build a panel/region dict from a bottom-up figure-fraction bbox.

    All values are native Python ``float`` so the report is plain/JSON-able
    (matplotlib hands back ``np.float64`` positions).
    """
    x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)
    w_frac, h_frac = x1 - x0, y1 - y0
    return {
        "x_frac": x0,
        "y_frac": 1.0 - y1,  # top-down
        "w_frac": w_frac,
        "h_frac": h_frac,
        "x_mm": x0 * cw,
        "y_mm": (1.0 - y1) * ch,
        "w_mm": w_frac * cw,
        "h_mm": h_frac * ch,
        "area_frac": w_frac * h_frac,
        "area_mm2": (w_frac * cw) * (h_frac * ch),
    }


def _empty_regions(
    boxes: List[Tuple[float, float, float, float]],
    cw: float,
    ch: float,
    min_area_frac: float = 0.004,
) -> List[Dict]:
    """Maximal blank rectangles of the canvas not covered by any panel box.

    Builds the arrangement from the distinct x/y edges of all panels (+ canvas
    bounds), marks each cell covered/blank by its centre, then greedily merges
    adjacent blank cells into maximal rectangles. Slivers below ``min_area_frac``
    are dropped.
    """
    if not boxes:
        return []
    xs = sorted({0.0, 1.0, *(b[0] for b in boxes), *(b[2] for b in boxes)})
    ys = sorted({0.0, 1.0, *(b[1] for b in boxes), *(b[3] for b in boxes)})
    ncols = len(xs) - 1
    nrows = len(ys) - 1
    covered = [[False] * ncols for _ in range(nrows)]
    for j in range(nrows):
        cy = (ys[j] + ys[j + 1]) / 2.0
        for i in range(ncols):
            cx = (xs[i] + xs[i + 1]) / 2.0
            covered[j][i] = any(
                b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boxes
            )
    used = [[False] * ncols for _ in range(nrows)]
    regions: List[Dict] = []
    for j in range(nrows):
        for i in range(ncols):
            if covered[j][i] or used[j][i]:
                continue
            i2 = i
            while i2 + 1 < ncols and not covered[j][i2 + 1] and not used[j][i2 + 1]:
                i2 += 1
            j2 = j
            while j2 + 1 < nrows and all(
                not covered[j2 + 1][ii] and not used[j2 + 1][ii]
                for ii in range(i, i2 + 1)
            ):
                j2 += 1
            for jj in range(j, j2 + 1):
                for ii in range(i, i2 + 1):
                    used[jj][ii] = True
            region = _box_panel(xs[i], ys[j], xs[i2 + 1], ys[j2 + 1], cw, ch)
            if region["area_frac"] >= min_area_frac:
                regions.append(region)
    return regions


def layout_report(fig: Any) -> Dict[str, Any]:
    """Structured, machine-readable layout of a composed figure.

    Returns a dict with: ``mode`` (grid/mm/tiled when known), ``canvas_mm``,
    ``panels`` (per-panel ``*_frac``/``*_mm`` box + ``aspect``), ``empty_regions``
    (maximal blank rectangles), and ``coverage_frac`` (fraction of the canvas
    covered by panels). An agent reads this to propose panel target sizes for a
    tight, no-stretch re-tiling.
    """
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    record = getattr(fig, "record", None)

    canvas_mm = getattr(record, "canvas_size_mm", None)
    if canvas_mm:
        cw, ch = float(canvas_mm[0]), float(canvas_mm[1])
    else:
        w_in, h_in = mpl_fig.get_size_inches()
        cw, ch = float(w_in) * 25.4, float(h_in) * 25.4

    panels: List[Dict] = []
    boxes: List[Tuple[float, float, float, float]] = []
    for ax in mpl_fig.axes:
        if not ax.get_visible():
            continue
        pos = ax.get_position()
        box = (pos.x0, pos.y0, pos.x1, pos.y1)
        boxes.append(box)
        panel = _box_panel(*box, cw, ch)
        panel["aspect"] = panel["w_mm"] / panel["h_mm"] if panel["h_mm"] > 0 else None
        panels.append(panel)

    empty_regions = _empty_regions(boxes, cw, ch)
    coverage_frac = sum(p["area_frac"] for p in panels)

    return {
        "mode": getattr(record, "composition_mode", None) or "grid",
        "canvas_mm": (cw, ch),
        "panels": panels,
        "empty_regions": empty_regions,
        "coverage_frac": coverage_frac,
    }
