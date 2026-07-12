#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tiled (row-justified, whitespace-free) composition layout.

This is the publication-grade layout mode for ``fr.compose``: it places
panels in a list of rows (like ``patchwork`` / ``svgutils`` justified grids)
so that

* every panel keeps its TRUE aspect ratio (no stretching),
* within a row all panels share ONE common height and sit edge-to-edge
  (only ``gap_mm`` between them) -> no intra-row whitespace,
* every row spans the SAME overall content width ``W`` -> no ragged right
  edge.

The geometry it produces is emitted as the existing mm-based ``sources``
dict (``{path: {"xy_mm", "size_mm"}}``) and the placement itself is then
delegated to :func:`figrecipe._composition._compose._compose_mm_based`, so a
tiled figure round-trips through save/reproduce exactly like any other
mm-based composition (no new placement/serialization code path).

Coordinate origin
-----------------
``_compose_mm_based`` treats ``xy_mm`` with **y=0 at the TOP**, increasing
downward (``panel_bottom = 1 - (y + h) / canvas_h``). Rows are therefore
stacked by increasing ``y_mm`` and the FIRST layout row (``y_mm = 0``) is
rendered visually on top, matching the way the layout reads on the page.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

# Aspect ratio (w / h) used only when a source carries neither a content size,
# a figsize, nor a readable PNG -- a last-resort square so layout never crashes.
_FALLBACK_ASPECT = 1.0


def _is_tiled_layout(layout: Any, sources: Dict[Any, Any]) -> bool:
    """Return True when ``layout``/``sources`` describe a TILED composition.

    A tiled call is recognised by a ``layout`` that is either a multiline
    string (rows split on newlines, labels on whitespace) or a list whose
    items are themselves lists of string labels, paired with a ``sources``
    dict keyed by those string labels (``{"A": "a.yaml", ...}``).

    Grid mode (``layout=(nrows, ncols)``, integer tuple) and mm mode
    (``sources={path: {"xy_mm": ...}}``) are intentionally NOT matched here.
    """
    if not sources:
        return False

    # sources must be keyed by str labels (grid uses tuple keys; mm uses paths
    # whose VALUES are {"xy_mm": ...} dicts -- exclude that explicitly).
    first_key = next(iter(sources.keys()))
    if not isinstance(first_key, str):
        return False
    first_value = sources[first_key]
    if isinstance(first_value, dict) and "xy_mm" in first_value:
        return False  # this is mm-based, not tiled

    if isinstance(layout, str):
        return True
    if isinstance(layout, (list, tuple)):
        # list of ROWS, each row a list/tuple of str labels.
        return (
            all(
                isinstance(row, (list, tuple))
                and len(row) > 0
                and all(isinstance(lab, str) for lab in row)
                for row in layout
            )
            and len(layout) > 0
        )
    return False


def _parse_layout(layout: Union[str, List[List[str]]]) -> List[List[str]]:
    """Normalise a layout spec into a list of rows of label strings.

    Accepts either a multiline string (``"A B C\\nD"`` -> rows split on
    newlines, labels on whitespace) or an already-structured list of lists.
    Blank lines in a string layout are skipped.
    """
    if isinstance(layout, str):
        rows: List[List[str]] = []
        for line in layout.splitlines():
            labels = line.split()
            if labels:
                rows.append(labels)
        return rows
    return [list(row) for row in layout]


def _validate_layout(rows: List[List[str]], sources: Dict[str, Any]) -> None:
    """Fail loud (ValueError) on any label/source mismatch or empty row.

    No silent fallback: every label in the layout must have a source and
    every source must be referenced by the layout, exactly once is not
    required but presence both ways is.
    """
    if not rows:
        raise ValueError(
            "tiled layout is empty: provide at least one row of panel labels."
        )
    for r, row in enumerate(rows):
        if not row:
            raise ValueError(f"tiled layout row {r} is empty (no panel labels).")

    layout_labels = [lab for row in rows for lab in row]
    layout_set = set(layout_labels)
    source_set = set(sources.keys())

    missing_sources = layout_set - source_set
    if missing_sources:
        raise ValueError(
            "tiled layout references labels with no matching source: "
            f"{sorted(missing_sources)}. sources has: {sorted(source_set)}."
        )
    unused_sources = source_set - layout_set
    if unused_sources:
        raise ValueError(
            "sources provides labels not placed in the layout: "
            f"{sorted(unused_sources)}. layout uses: {sorted(layout_set)}."
        )
    duplicates = [lab for lab in layout_set if layout_labels.count(lab) > 1]
    if duplicates:
        raise ValueError(
            f"tiled layout places label(s) more than once: {sorted(duplicates)}."
        )


def _source_aspect(source_spec: Any) -> float:
    """Return a panel's true aspect ratio ``content_w_mm / content_h_mm``.

    Resolution order (each a real measurement of the saved panel, never a
    guess unless all fail):

    1. ``record.content_size_mm`` -- the tight cropped content [w, h] in mm.
    2. ``record.figsize`` -- the figure's [w, h] in inches.
    3. the saved PNG's pixel aspect (companion image of a recipe, or a raw
       image source).
    4. ``_FALLBACK_ASPECT`` (square) -- only if none of the above exist.
    """
    from ._source_parser import parse_source_spec_with_path

    record, _ax_key, path = parse_source_spec_with_path(source_spec)

    csm = getattr(record, "content_size_mm", None)
    if csm and len(csm) == 2 and csm[1]:
        return float(csm[0]) / float(csm[1])

    figsize = getattr(record, "figsize", None)
    if figsize and len(figsize) == 2 and figsize[1]:
        return float(figsize[0]) / float(figsize[1])

    aspect = _png_aspect(path)
    if aspect is not None:
        return aspect

    return _FALLBACK_ASPECT


def _source_content_width_mm(source_spec: Any, aspect: float) -> float:
    """Return a panel's true content WIDTH in mm (for the default-``W`` rule).

    Prefers the recorded ``content_size_mm[0]``; else derives a width from the
    figsize inches; else from the PNG pixels at 300 dpi; else falls back to a
    width implied by ``aspect`` at a nominal 45 mm height so the default still
    produces a sane canvas.
    """
    from ._source_parser import parse_source_spec_with_path

    record, _ax_key, path = parse_source_spec_with_path(source_spec)

    csm = getattr(record, "content_size_mm", None)
    if csm and len(csm) == 2 and csm[0]:
        return float(csm[0])

    figsize = getattr(record, "figsize", None)
    if figsize and len(figsize) == 2 and figsize[0]:
        return float(figsize[0]) * 25.4

    width_px = _png_size_px(path)
    if width_px is not None:
        return width_px[0] / 300.0 * 25.4

    return aspect * 45.0


def _png_size_px(path):
    """Return (width_px, height_px) of an image/companion PNG, or None."""
    if path is None:
        return None
    p = Path(path)
    # A recipe path -> look for a sibling PNG with the same stem.
    if p.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".tif",
        ".bmp",
        ".gif",
        ".webp",
    }:
        p = p.with_suffix(".png")
    if not p.exists():
        return None
    try:
        from PIL import Image

        with Image.open(p) as img:
            return (img.width, img.height)
    except Exception:
        return None


def _png_aspect(path):
    """Return width/height aspect of an image/companion PNG, or None."""
    size = _png_size_px(path)
    if size is None or not size[1]:
        return None
    return size[0] / size[1]


def _row_height_mm(aspects: List[float], width_mm: float, gap_mm: float) -> float:
    """Return the ONE common row height (mm) for panels of ``aspects`` in a row.

    This is the single formula shared by :func:`build_tiled_sources` (which
    resolves aspects from real ``sources``) and the auto-tiler (which packs
    raw aspect ratios before any source exists) -- factored out here so both
    callers compute row geometry identically (no drift between the two).

    ``h_r = (width_mm - (k-1) * gap_mm) / sum(aspects)`` where ``k =
    len(aspects)``; each panel's width is then ``aspect_i * h_r`` (never
    stretched -- see :func:`_row_panel_widths_mm`).
    """
    k = len(aspects)
    avail = width_mm - (k - 1) * gap_mm
    sum_aspect = sum(aspects)
    return avail / sum_aspect if sum_aspect else avail


def _row_panel_widths_mm(aspects: List[float], row_height_mm: float) -> List[float]:
    """Return each panel's true width (mm) at the row's common height.

    ``width_i = aspect_i * row_height_mm`` -- the panel is drawn at its own
    aspect ratio, never stretched to fill leftover space.
    """
    return [a * row_height_mm for a in aspects]


def build_tiled_sources(
    layout: Union[str, List[List[str]]],
    sources: Dict[str, Any],
    width_mm: float = None,
    gap_mm: float = 1.0,
) -> Tuple[Dict[str, Dict[str, Any]], Tuple[float, float]]:
    """Compute the mm-based placement for a TILED (row-justified) layout.

    This is the layout algorithm (the actual point of the tiled mode); it
    returns geometry only -- the caller delegates the resulting dict to
    ``_compose_mm_based`` for placement so the figure round-trips.

    Parameters
    ----------
    layout : str or list of list of str
        Rows of panel labels. ``"A B C\\nD"`` or ``[["A","B","C"],["D"]]``.
    sources : dict
        ``{label: source}`` where each source is a recipe path / image path /
        ``FigureRecord`` / ``(source, ax_key)`` tuple, as accepted by the
        mm-based composer.
    width_mm : float, optional
        Overall content width ``W`` of the figure in mm. When omitted, the
        DEFAULT is ``W = max over rows of (sum of the row's TRUE content
        widths + (k-1) * gap_mm)`` -- i.e. the widest row at its natural size
        sets the figure width and no panel is ever upscaled past its true
        size on the widest row.
    gap_mm : float
        Gutter between adjacent panels (both within a row and between rows).
        ``0`` makes panels share edges exactly.

    Returns
    -------
    sources_mm : dict
        ``{source: {"xy_mm": (x, y), "size_mm": (w, h)}}`` ready for
        ``_compose_mm_based``. ``xy_mm`` uses y=0 at the top so the first
        layout row is on top.
    canvas_size_mm : tuple
        ``(W, total_height)`` of the composed canvas in mm.

    Notes
    -----
    For a row with panels of aspects ``a_i`` (i = 1..k) the row is given one
    common height ``h_r = (W - (k-1) * gap_mm) / sum(a_i)``; each panel is
    then ``width_i = a_i * h_r`` wide. Summed, the panels plus gaps fill
    exactly ``W``, so the row has no internal whitespace and no ragged edge.
    """
    rows = _parse_layout(layout)
    _validate_layout(rows, sources)

    # Measure every panel once: aspect (for justification) and true width
    # (for the default-W rule).
    aspect_of: Dict[str, float] = {}
    width_of: Dict[str, float] = {}
    for label, spec in sources.items():
        a = _source_aspect(spec)
        aspect_of[label] = a
        width_of[label] = _source_content_width_mm(spec, a)

    # 1. Choose overall content width W.
    # TODO(title-clip): W accounts only for panel INK width, so the widest
    # panel's right edge sits flush at x=W (and the leftmost at x=0). A panel
    # TITLE is drawn point-sized and centered over its axes; when it is wider
    # than its panel it overhangs the panel edge, and on the outermost panels
    # that overhang crosses the canvas boundary and clips (the save-time crop
    # uses only a fixed 1mm margin, which does not scale with title length).
    # A clean fix must NOT perturb the geometry contract the tiled tests assert
    # (every row spans exactly W; adjacent panels share edges to 1e-6) -- e.g.
    # measure each row's title text overhang and expand the crop margin (not W)
    # to cover it, or expose a symmetric title_inset_mm. Left as a cosmetic
    # follow-up so it does not block the consolidation.
    if width_mm is not None:
        W = float(width_mm)
    else:
        W = 0.0
        for row in rows:
            row_natural = sum(width_of[lab] for lab in row) + (len(row) - 1) * gap_mm
            W = max(W, row_natural)

    # 2-3. Lay out each row at one common height, then stack top-to-bottom.
    sources_mm: Dict[str, Dict[str, Any]] = {}
    y = 0.0
    row_heights: List[float] = []
    for r, row in enumerate(rows):
        row_aspects = [aspect_of[lab] for lab in row]
        h_r = _row_height_mm(row_aspects, W, gap_mm)
        row_widths = _row_panel_widths_mm(row_aspects, h_r)
        row_heights.append(h_r)

        x = 0.0
        for lab, w_i in zip(row, row_widths):
            sources_mm[sources[lab]] = {
                "xy_mm": (x, y),
                "size_mm": (w_i, h_r),
            }
            x += w_i + gap_mm
        y += h_r + gap_mm

    total_height = sum(row_heights) + (len(rows) - 1) * gap_mm
    return sources_mm, (W, total_height)


__all__ = [
    "build_tiled_sources",
    "_is_tiled_layout",
    "_row_height_mm",
    "_row_panel_widths_mm",
]

# EOF
