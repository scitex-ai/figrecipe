#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-tiler: bin-pack panel ASPECT RATIOS into a tight, whitespace-free grid.

Where :func:`figrecipe._composition._tile.build_tiled_sources` places panels
whose row assignment (``layout``) is already known, :func:`auto_tile_layout`
answers the prior question -- GIVEN only each panel's true aspect ratio (no
source, no render), how many rows should there be and which labels go in
which row so the resulting canvas is as tight as possible (a target height)
or wastes as little area as possible (no target height)? Its output is a
``layout`` row-list in the EXACT format :func:`build_tiled_sources` consumes,
so the two functions compose directly:

    layout, sizes_mm, canvas_mm = auto_tile_layout(aspects, width_mm=180)
    # ... re-author/re-plot each panel at sizes_mm[label] ...
    sources_mm, canvas_mm = build_tiled_sources(layout, sources, width_mm=180)

This module never renders or resizes a panel itself -- it only proposes
geometry. Panels keep their true aspect ratio by construction (a row's
common height ``h_r`` derived once, each panel's width ``aspect_i * h_r`` --
see :func:`figrecipe._composition._tile._row_height_mm`), so "auto-tiling"
never means "stretch to fit": that is a hard invariant, not a best-effort one.
"""

from typing import Dict, List, Tuple

from ._tile import _row_height_mm, _row_panel_widths_mm

__all__ = ["auto_tile_layout"]


def _greedy_partition(
    labels_by_aspect_desc: List[str],
    aspects: Dict[str, float],
    n_rows: int,
) -> List[List[str]]:
    """Multi-way partition of labels into ``n_rows`` rows (LPT-greedy).

    Visits labels largest-aspect-first (Longest-Processing-Time-first, the
    standard greedy for multiway partition / multiprocessor scheduling) and
    drops each one into whichever row currently has the SMALLEST running
    aspect-sum. Balancing the aspect-sum (not the panel COUNT) keeps row
    heights close to parity -- see :func:`_row_height_mm`, where a row's
    height is inversely proportional to its aspect-sum -- so this avoids one
    very tall/skinny row sitting next to a very short/wide one.

    Ties (equal running sums) break by lowest row index, which also
    guarantees every one of the ``n_rows <= len(labels)`` rows receives at
    least one label (the first ``n_rows`` labels each land in a still-empty
    row before any row's sum grows past zero).
    """
    rows: List[List[str]] = [[] for _ in range(n_rows)]
    row_sums = [0.0] * n_rows
    for label in labels_by_aspect_desc:
        idx = min(range(n_rows), key=lambda i: (row_sums[i], i))
        rows[idx].append(label)
        row_sums[idx] += aspects[label]
    return rows


def _row_geometry(
    rows: List[List[str]],
    aspects: Dict[str, float],
    width_mm: float,
    gap_mm: float,
) -> Tuple[Dict[str, Tuple[float, float]], float]:
    """Apply the shared row-height formula to every row of a candidate layout.

    Returns ``(sizes_mm, total_height_mm)`` using the IDENTICAL
    ``_row_height_mm`` / ``_row_panel_widths_mm`` helpers that
    :func:`figrecipe._composition._tile.build_tiled_sources` uses, so a
    proposed layout's sizes never drift from what actually placing it would
    produce.
    """
    sizes_mm: Dict[str, Tuple[float, float]] = {}
    row_heights: List[float] = []
    for row in rows:
        row_aspects = [aspects[lab] for lab in row]
        h_r = _row_height_mm(row_aspects, width_mm, gap_mm)
        row_widths = _row_panel_widths_mm(row_aspects, h_r)
        for lab, w_i in zip(row, row_widths):
            sizes_mm[lab] = (w_i, h_r)
        row_heights.append(h_r)
    total_height = sum(row_heights) + (len(rows) - 1) * gap_mm
    return sizes_mm, total_height


def auto_tile_layout(
    aspects: Dict[str, float],
    width_mm: float,
    height_mm: float = None,
    gap_mm: float = 1.0,
) -> Tuple[List[List[str]], Dict[str, Tuple[float, float]], Tuple[float, float]]:
    """Bin-pack panel aspect ratios into a tight ``layout`` for ``build_tiled_sources``.

    Parameters
    ----------
    aspects : dict
        ``{label: w/h}`` -- each panel's TRUE aspect ratio. Never a size to
        target; only a ratio the packer must preserve exactly.
    width_mm : float
        Overall content width ``W`` of the figure in mm (same role as
        ``build_tiled_sources``'s ``width_mm``).
    height_mm : float, optional
        Target overall canvas height in mm. When given, the packer searches
        row-counts and picks the one whose resulting total height is closest
        to ``height_mm`` without exceeding it (falling back to the closest
        overall if every candidate exceeds it). When omitted, the packer
        instead MINIMISES wasted canvas area (the ``width_mm x total_height``
        bounding box minus the summed true panel areas) -- the canonical
        packing-efficiency objective.
    gap_mm : float
        Gutter between adjacent panels (both within a row and between rows),
        same convention as ``build_tiled_sources``.

    Returns
    -------
    layout : list of list of str
        Row-list of labels, ready to hand to ``build_tiled_sources`` (or
        ``fr.compose``) verbatim.
    sizes_mm : dict
        ``{label: (width_mm, height_mm)}`` -- the target size each panel
        should be RE-AUTHORED/re-plotted at. Every panel's ``w/h`` here
        equals ``aspects[label]`` exactly (to floating-point precision):
        this function only ever proposes geometry, it never stretches or
        upscales a panel.
    canvas_size_mm : tuple
        ``(width_mm, total_height_mm)`` of the resulting canvas.

    Notes
    -----
    For each candidate row-count ``n_rows`` (searched over ``1..len(aspects)``)
    labels are greedily partitioned by :func:`_greedy_partition` (largest
    aspect first, into whichever row has the smallest running aspect-sum --
    this keeps row heights close to parity). Each row is then sized by the
    SAME formula ``build_tiled_sources`` uses (see
    ``figrecipe._composition._tile._row_height_mm``): row height ``h_r =
    (width_mm - (k-1) * gap_mm) / sum(row aspects)``, panel width ``w_i =
    aspect_i * h_r``. Row order (top-to-bottom) and each row's internal label
    order follow assignment order and are never reshuffled afterwards.
    """
    if not aspects:
        raise ValueError("auto_tile_layout requires at least one panel in `aspects`.")

    labels = list(aspects.keys())
    n = len(labels)
    labels_by_aspect_desc = sorted(labels, key=lambda lab: aspects[lab], reverse=True)

    candidates: List[Tuple[List[List[str]], Dict[str, Tuple[float, float]], float]] = []
    for n_rows in range(1, n + 1):
        rows = _greedy_partition(labels_by_aspect_desc, aspects, n_rows)
        sizes_mm, total_height = _row_geometry(rows, aspects, width_mm, gap_mm)
        candidates.append((rows, sizes_mm, total_height))

    if height_mm is not None:
        # Closest-without-exceeding when possible, else closest overall.
        fitting = [c for c in candidates if c[2] <= height_mm + 1e-9]
        best = (
            max(fitting, key=lambda c: c[2])
            if fitting
            else min(candidates, key=lambda c: abs(c[2] - height_mm))
        )
    else:

        def _wasted_area(
            candidate: Tuple[List[List[str]], Dict[str, Tuple[float, float]], float],
        ) -> float:
            _rows, sizes_mm, total_height = candidate
            occupied = sum(w * h for w, h in sizes_mm.values())
            return width_mm * total_height - occupied

        best = min(candidates, key=_wasted_area)

    rows, sizes_mm, total_height = best
    return rows, sizes_mm, (float(width_mm), float(total_height))


# EOF
