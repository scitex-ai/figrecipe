#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout-related auto-fix functions for Diagram diagrams.

Fixes container enclosure (R1), box overlaps (R2), and canvas bounds (R9).
"""

from itertools import combinations
from typing import TYPE_CHECKING, Dict, List

from ._geom import box_rect, rects_overlap

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ._core import Diagram

# Margin added beyond the exact fix to prevent borderline re-violations.
_FIX_MARGIN_MM = 3.0
# Per-side inner padding when expanding containers to enclose children.
_CONTAINER_PAD_MM = 8.0


# ── Collectors ──────────────────────────────────────────────────────


def _collect_container_violations(diagram: "Diagram") -> List[Dict]:
    """Collect all R1 container-enclosure violations."""
    results = []
    for cid, container in diagram._containers.items():
        if cid not in diagram._positions:
            continue
        cpos = diagram._positions[cid]
        cl = cpos.x_mm - cpos.width_mm / 2
        cr = cpos.x_mm + cpos.width_mm / 2
        cb = cpos.y_mm - cpos.height_mm / 2
        ct = cpos.y_mm + cpos.height_mm / 2
        for child_id in container.get("children", []):
            if child_id not in diagram._positions:
                continue
            ch = diagram._positions[child_id]
            chl = ch.x_mm - ch.width_mm / 2
            chr_ = ch.x_mm + ch.width_mm / 2
            chb = ch.y_mm - ch.height_mm / 2
            cht = ch.y_mm + ch.height_mm / 2
            excess = {
                "left": max(0, cl - chl),
                "right": max(0, chr_ - cr),
                "bottom": max(0, cb - chb),
                "top": max(0, cht - ct),
            }
            if any(v > 0 for v in excess.values()):
                results.append(
                    {"container_id": cid, "child_id": child_id, "excess": excess}
                )
    return results


def _collect_overlap_violations(diagram: "Diagram") -> List[Dict]:
    """Collect all R2 box-overlap violations."""
    results = []
    box_ids = [bid for bid in diagram._boxes if bid in diagram._positions]
    for id_a, id_b in combinations(box_ids, 2):
        r_a = box_rect(diagram._positions[id_a])
        r_b = box_rect(diagram._positions[id_b])
        if rects_overlap(r_a, r_b):
            results.append(
                {
                    "id_a": id_a,
                    "id_b": id_b,
                    "overlap_x": min(r_a[2], r_b[2]) - max(r_a[0], r_b[0]),
                    "overlap_y": min(r_a[3], r_b[3]) - max(r_a[1], r_b[1]),
                }
            )
    return results


def _collect_canvas_violations(diagram: "Diagram") -> List[Dict]:
    """Collect all R9 canvas-bounds violations."""
    x_lo, x_hi = diagram.xlim
    y_lo, y_hi = diagram.ylim
    results = []
    for eid in list(diagram._boxes) + list(diagram._containers):
        if eid not in diagram._positions:
            continue
        left, bottom, right, top = box_rect(diagram._positions[eid])
        excess = {
            "left": max(0, x_lo - left),
            "right": max(0, right - x_hi),
            "bottom": max(0, y_lo - bottom),
            "top": max(0, top - y_hi),
        }
        if any(v > 0 for v in excess.values()):
            results.append({"id": eid, "excess": excess})
    return results


# ── Fixers ──────────────────────────────────────────────────────────


def fix_container_enclosure(diagram: "Diagram") -> int:
    """R1: Expand containers to enclose children and center them. Returns fix count."""
    violations = _collect_container_violations(diagram)
    if not violations:
        return 0
    # Aggregate max excess per container across all children.
    per_container: Dict[str, Dict[str, float]] = {}
    for v in violations:
        cid = v["container_id"]
        if cid not in per_container:
            per_container[cid] = {"left": 0, "right": 0, "bottom": 0, "top": 0}
        for edge in ("left", "right", "bottom", "top"):
            per_container[cid][edge] = max(per_container[cid][edge], v["excess"][edge])
    for cid, excess in per_container.items():
        pos = diagram._positions[cid]
        pad = _CONTAINER_PAD_MM
        grow_w = excess["left"] + excess["right"] + 2 * pad
        grow_h = excess["bottom"] + excess["top"] + 2 * pad
        pos.width_mm += grow_w
        pos.height_mm += grow_h
        pos.x_mm += (excess["right"] - excess["left"]) / 2
        pos.y_mm += (excess["top"] - excess["bottom"]) / 2
        sides = [s for s, v in excess.items() if v > 0]
        logger.warning(
            "  R1 container_enclosure: '%s' expanded +%.1f×%.1fmm (%s)",
            cid,
            grow_w,
            grow_h,
            ",".join(sides),
        )

    # Center children within their (now-expanded) containers.
    _TITLE_RESERVE_MM = 8.0  # vertical space for container title
    for cid in per_container:
        cpos = diagram._positions[cid]
        children = diagram._containers[cid].get("children", [])
        child_positions = [
            diagram._positions[ch] for ch in children if ch in diagram._positions
        ]
        if not child_positions:
            continue
        # Bounding box of all children
        min_x = min(ch.x_mm - ch.width_mm / 2 for ch in child_positions)
        max_x = max(ch.x_mm + ch.width_mm / 2 for ch in child_positions)
        min_y = min(ch.y_mm - ch.height_mm / 2 for ch in child_positions)
        max_y = max(ch.y_mm + ch.height_mm / 2 for ch in child_positions)
        group_cx = (min_x + max_x) / 2
        group_cy = (min_y + max_y) / 2
        # Container inner center (shifted down to account for title)
        inner_cx = cpos.x_mm
        inner_cy = cpos.y_mm - _TITLE_RESERVE_MM / 2
        # Shift all children
        dx = inner_cx - group_cx
        dy = inner_cy - group_cy
        for ch in child_positions:
            ch.x_mm += dx
            ch.y_mm += dy
    return len(per_container)


def fix_overlaps(diagram: "Diagram") -> int:
    """R2: Push overlapping boxes apart. Returns fix count."""
    violations = _collect_overlap_violations(diagram)
    if not violations:
        return 0
    for v in violations:
        logger.warning(
            "  R2 overlap: '%s' × '%s' (%.1f×%.1fmm)",
            v["id_a"],
            v["id_b"],
            v["overlap_x"],
            v["overlap_y"],
        )
    from ._overlap import resolve_overlaps

    x_lo, x_hi = diagram.xlim
    y_lo, y_hi = diagram.ylim
    resolve_overlaps(
        diagram, gap=_FIX_MARGIN_MM, x_min=x_lo, x_max=x_hi, y_min=y_lo, y_max=y_hi
    )
    return len(violations)


def fix_canvas_bounds(diagram: "Diagram") -> int:
    """R9: Expand canvas xlim/ylim to encompass all elements. Returns fix count."""
    violations = _collect_canvas_violations(diagram)
    if not violations:
        return 0
    x_lo, x_hi = diagram.xlim
    y_lo, y_hi = diagram.ylim
    for v in violations:
        excess = v["excess"]
        sides = [
            f"{s}={excess[s]:.1f}"
            for s in ("left", "right", "bottom", "top")
            if excess[s] > 0
        ]
        logger.warning(
            "  R9 canvas_bounds: '%s' exceeds (%s)", v["id"], ", ".join(sides)
        )
        x_lo -= excess["left"] + _FIX_MARGIN_MM if excess["left"] > 0 else 0
        x_hi += excess["right"] + _FIX_MARGIN_MM if excess["right"] > 0 else 0
        y_lo -= excess["bottom"] + _FIX_MARGIN_MM if excess["bottom"] > 0 else 0
        y_hi += excess["top"] + _FIX_MARGIN_MM if excess["top"] > 0 else 0
    diagram.xlim = (x_lo, x_hi)
    diagram.ylim = (y_lo, y_hi)
    diagram.width_mm = x_hi - x_lo
    diagram.height_mm = y_hi - y_lo
    return len(violations)
