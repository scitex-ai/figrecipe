#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Named grid aliases for ``fr.compose`` layouts.

Card figrecipe-bioinformatics-figure-beauty-20261006, source-adoption phase:
the last mapped-but-open item -- layout presets as named compose aliases.
Each alias resolves to a grid shape ``fr.compose`` already accepts
(``layout=(nrows, ncols)``), so this layer invents no geometry: it only
spells ``(1, 2)`` as ``"side_by_side"`` for call-site readability.

Tiled/bento layouts (``layout=[[...]]``, see ``_tile.py``) stay explicit --
they carry per-panel row assignment, which a bare grid name cannot express.
"""

from typing import Dict, Tuple

#: Alias -> grid shape consumable as ``compose(layout=...)``.
COMPOSE_LAYOUT_PRESETS: Dict[str, Tuple[int, int]] = {
    "single": (1, 1),
    "side_by_side": (1, 2),
    "stacked": (2, 1),
    "triptych": (1, 3),
    "quad": (2, 2),
}

_PRESET_DESCRIPTIONS: Dict[str, str] = {
    "single": "One panel filling the canvas",
    "side_by_side": "Two panels in one row (pairwise comparison)",
    "stacked": "Two panels in one column (vertical story)",
    "triptych": "Three panels in one row (three-way comparison)",
    "quad": "2x2 panel grid (four-condition comparison)",
}


def resolve_compose_preset(name: str) -> Tuple[int, int]:
    """Resolve a preset alias to its ``(nrows, ncols)`` grid shape."""
    return COMPOSE_LAYOUT_PRESETS[name]


def list_compose_presets() -> Dict[str, str]:
    """Map every preset alias to its one-line description."""
    return dict(_PRESET_DESCRIPTIONS)


__all__ = [
    "COMPOSE_LAYOUT_PRESETS",
    "resolve_compose_preset",
    "list_compose_presets",
]
