#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-parseable overlap reports.

Reports are produced by the three detectors and aggregated by
:func:`figrecipe._overlap.detect_overlaps`. The shape is stable so that
downstream linters / paper-prep skills can ingest them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class _OverlapItemBase:
    element_a: str
    element_b: str
    axes_key: Optional[str] = None
    severity: str = "warn"  # 'warn' or 'error'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShapeOverlapReport(_OverlapItemBase):
    """One geometric overlap between two elements."""

    overlap_pixels: int = 0
    overlap_fraction: float = 0.0
    region_bbox: Optional[Tuple[int, int, int, int]] = None  # (x1,y1,x2,y2)
    kind: str = "shape"


@dataclass
class ColorOverlapReport(_OverlapItemBase):
    """Two distinguishable elements drawn with indistinguishable colors."""

    delta_e: float = 0.0  # CIEDE2000 distance
    threshold: float = 5.0
    color_a_rgb: Optional[Tuple[float, float, float]] = None
    color_b_rgb: Optional[Tuple[float, float, float]] = None
    shared_color_summary: str = ""
    region_summary: str = ""
    kind: str = "color"


@dataclass
class LegendOverlapReport(_OverlapItemBase):
    """Legend bbox collides with data artist."""

    legend_bbox_axes: Optional[Tuple[float, float, float, float]] = None
    fallback_applied: bool = False
    final_loc: Optional[str] = None
    final_bbox_to_anchor: Optional[Tuple[float, float]] = None
    kind: str = "legend"


@dataclass
class OverlapReport:
    """Aggregated detector output for one figure save / audit call."""

    shape: List[ShapeOverlapReport] = field(default_factory=list)
    color: List[ColorOverlapReport] = field(default_factory=list)
    legend: List[LegendOverlapReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shape": [r.to_dict() for r in self.shape],
            "color": [r.to_dict() for r in self.color],
            "legend": [r.to_dict() for r in self.legend],
        }

    def is_clean(self) -> bool:
        return not (self.shape or self.color or self.legend)

    def has_errors(self) -> bool:
        return any(r.severity == "error" for r in self._all())

    def warnings(self) -> List[_OverlapItemBase]:
        return [r for r in self._all() if r.severity == "warn"]

    def errors(self) -> List[_OverlapItemBase]:
        return [r for r in self._all() if r.severity == "error"]

    def _all(self) -> List[_OverlapItemBase]:
        return list(self.shape) + list(self.color) + list(self.legend)


__all__ = [
    "ShapeOverlapReport",
    "ColorOverlapReport",
    "LegendOverlapReport",
    "OverlapReport",
]
