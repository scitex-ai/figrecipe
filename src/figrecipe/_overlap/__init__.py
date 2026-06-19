#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe overlap detection package.

Three detectors share the same hitmap infrastructure:

* :mod:`._shape`  — geometric overlap between rendered elements
  (default: ``error``; opt-in ``warn`` for KDE / density / intentional
  overlays).
* :mod:`._color`  — perceptually-close colors (CIEDE2000 < 5) on
  spatially-adjacent or overlapping elements (default: ``warn``).
* :mod:`._legend` — legend bbox vs data-element collision with a loud
  warning + auto-fallback to outside-axes placement.

The single shared :func:`._hitmap.build_element_hitmap` wraps the
existing per-element-ID rendering from
``figrecipe._editor._hitmap.generate_hitmap``.
"""

from ._core import detect_overlaps, run_overlap_audit
from ._errors import OverlapError
from ._policy import OverlapPolicy, resolve_policy
from ._report import (
    ColorOverlapReport,
    LegendOverlapReport,
    OverlapReport,
    ShapeOverlapReport,
)

__all__ = [
    "OverlapError",
    "OverlapPolicy",
    "resolve_policy",
    "OverlapReport",
    "ShapeOverlapReport",
    "ColorOverlapReport",
    "LegendOverlapReport",
    "detect_overlaps",
    "run_overlap_audit",
]
