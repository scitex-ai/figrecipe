#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carry per-source panel captions forward into a composed figure.

When ``compose()`` is called without explicit ``panel_captions``, each source
panel's own ``record.caption`` should become its ``(A)/(B)/...`` entry on the
composed figure — otherwise composed figures silently drop panel captions (the
same gap class as composed colorbars). These helpers assemble that list from
the per-source captions collected during composition.
"""

from typing import Dict, List, Optional, Tuple

__all__ = ["auto_panel_captions_grid", "auto_panel_captions_seq"]


def _nonempty(cap: Optional[str]) -> bool:
    return bool(cap and str(cap).strip())


def auto_panel_captions_grid(
    source_captions: Dict[Tuple[int, int], Optional[str]],
    nrows: int,
    ncols: int,
) -> Optional[List[str]]:
    """Build a row-major panel-caption list from per-source captions.

    Index ``row * ncols + col`` matches the flattened (row-major) axes order
    that ``render_compose_captions`` iterates, so each cell's caption lands on
    the right panel. Missing/empty cells become ``""`` (rendered as a no-op).
    Returns ``None`` when no source carried a caption, leaving compose's
    caption rendering a no-op exactly as before.
    """
    if not any(_nonempty(c) for c in source_captions.values()):
        return None
    out: List[str] = []
    for row in range(nrows):
        for col in range(ncols):
            cap = source_captions.get((row, col))
            out.append(str(cap).strip() if _nonempty(cap) else "")
    return out


def auto_panel_captions_seq(
    captions: List[Optional[str]],
    axis_counts: List[int],
) -> Optional[List[str]]:
    """Build a panel-caption list for sequential (mm/tiled) composition.

    Only safe when every source contributed exactly one axes — otherwise the
    one-caption-per-source mapping can't align with the per-axes label order,
    so we decline (return ``None``) and leave it to the caller. Returns
    ``None`` when no source carried a caption.
    """
    if any(n != 1 for n in axis_counts):
        return None
    if not any(_nonempty(c) for c in captions):
        return None
    return [str(c).strip() if _nonempty(c) else "" for c in captions]
