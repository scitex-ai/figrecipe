#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arrow-related auto-fix functions for Diagram diagrams.

Fixes arrow lengths, label placement (R8), occlusion (R7),
bidirectional splitting, and post-render label collisions (R5/R6).
"""

import math
from typing import TYPE_CHECKING, Dict, List

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ._core import Diagram

# Minimum visible gap between connected boxes for readable arrows.
_MIN_ARROW_GAP_MM = 15.0


# ── Collectors ──────────────────────────────────────────────────────


def _collect_label_side_violations(diagram: "Diagram") -> List[Dict]:
    """Collect all R8 arrow-label-side violations."""
    from ._validate import compute_arrow_label_position

    results = []
    for arrow in diagram._arrows:
        if not arrow.curve or not arrow.label:
            continue
        src_pos = diagram._positions.get(arrow.source)
        tgt_pos = diagram._positions.get(arrow.target)
        if not src_pos or not tgt_pos:
            continue
        if arrow.source_anchor == "auto" or arrow.target_anchor == "auto":
            auto_s, auto_t = diagram._auto_anchor(src_pos, tgt_pos)
            sa = auto_s if arrow.source_anchor == "auto" else arrow.source_anchor
            ta = auto_t if arrow.target_anchor == "auto" else arrow.target_anchor
        else:
            sa, ta = arrow.source_anchor, arrow.target_anchor
        start = diagram._get_anchor(src_pos, sa)
        end = diagram._get_anchor(tgt_pos, ta)
        lx, ly = compute_arrow_label_position(
            start, end, arrow.curve, arrow.label_offset_mm
        )
        dx, dy = end[0] - start[0], end[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            continue
        nx, ny = dy / dist, -dx / dist
        arc_side = (nx * arrow.curve, ny * arrow.curve)
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        dot = (lx - mx) * arc_side[0] + (ly - my) * arc_side[1]
        if dot < 0:
            results.append({"arrow": arrow, "current_curve": arrow.curve})
    return results


# ── Pre-render fixers ───────────────────────────────────────────────


def fix_arrow_lengths(diagram: "Diagram") -> int:
    """Ensure minimum visible gap between connected boxes for readable arrows.

    For each arrow, measures the rectangle-to-rectangle gap between source
    and target boxes. If shorter than _MIN_ARROW_GAP_MM, pushes the target
    box further along the source-to-target direction.

    Returns number of arrows whose connected boxes were pushed apart.
    """
    from matplotlib.transforms import Bbox

    from ._geom import bbox_gap

    fixed = 0
    for arrow in diagram._arrows:
        src = diagram._positions.get(arrow.source)
        tgt = diagram._positions.get(arrow.target)
        if not src or not tgt:
            continue
        dx = tgt.x_mm - src.x_mm
        dy = tgt.y_mm - src.y_mm
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            continue
        src_bb = Bbox(
            [
                [src.x_mm - src.width_mm / 2, src.y_mm - src.height_mm / 2],
                [src.x_mm + src.width_mm / 2, src.y_mm + src.height_mm / 2],
            ]
        )
        tgt_bb = Bbox(
            [
                [tgt.x_mm - tgt.width_mm / 2, tgt.y_mm - tgt.height_mm / 2],
                [tgt.x_mm + tgt.width_mm / 2, tgt.y_mm + tgt.height_mm / 2],
            ]
        )
        gap = bbox_gap(src_bb, tgt_bb)
        if gap >= _MIN_ARROW_GAP_MM:
            continue
        shortfall = _MIN_ARROW_GAP_MM - gap
        nx, ny = dx / dist, dy / dist
        tgt.x_mm += nx * shortfall
        tgt.y_mm += ny * shortfall
        logger.warning(
            "  arrow_length: '%s'->'%s' gap=%.1fmm < %.1fmm, pushed '%s' +%.1fmm",
            arrow.source,
            arrow.target,
            gap,
            _MIN_ARROW_GAP_MM,
            arrow.target,
            shortfall,
        )
        fixed += 1
    return fixed


def fix_arrow_labels(diagram: "Diagram") -> int:
    """R8: Flip curve sign so label is on same side as arc. Returns fix count."""
    violations = _collect_label_side_violations(diagram)
    for v in violations:
        a = v["arrow"]
        a.curve = -v["current_curve"]
        logger.warning(
            "  R8 arrow_label: '%s'->'%s' label='%s' curve flipped %.2f->%.2f",
            a.source,
            a.target,
            a.label,
            v["current_curve"],
            a.curve,
        )
    return len(violations)


def fix_bidirectional_arrows(diagram: "Diagram", curve: float = 0.4) -> int:
    """Offset bidirectional arrow pairs with opposite curves.

    Detects pairs where A->B and B->A both exist, then assigns
    opposite curve values so the arrows arc away from each other.
    Skips arrows where the user already set a non-zero curve.
    """
    pairs: Dict[tuple, list] = {}
    for a in diagram._arrows:
        key = tuple(sorted([a.source, a.target]))
        pairs.setdefault(key, []).append(a)
    fixed = 0
    for group in pairs.values():
        if len(group) < 2:
            continue
        for a in group:
            if a.curve != 0.0:
                continue  # User already set curve, respect it
            a.curve = curve
            logger.warning(
                "  bidirectional: '%s'->'%s' auto-curved %.2f",
                a.source,
                a.target,
                curve,
            )
            fixed += 1
    return fixed


# ── R7: Arrow occlusion auto-curve ─────────────────────────────────


def _arrow_visibility_prerender(diagram: "Diagram", arrow) -> float:
    """Compute visibility ratio for an arrow against intermediate boxes.

    Returns float in [0, 1]: 1.0 = fully visible, 0.0 = fully occluded.
    For curved arrows, approximates the arc as two segments via the
    midpoint offset (curve * dist perpendicular to the chord).
    """
    from ._geom import box_rect, seg_rect_clip_len

    src = diagram._positions.get(arrow.source)
    tgt = diagram._positions.get(arrow.target)
    if not src or not tgt:
        return 1.0
    dx, dy = tgt.x_mm - src.x_mm, tgt.y_mm - src.y_mm
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return 1.0
    # Build path: straight (2 pts) or curved (3 pts via midpoint offset)
    if arrow.curve and abs(arrow.curve) > 1e-6:
        nx, ny = -dy / dist, dx / dist  # perpendicular unit vector
        mx = (src.x_mm + tgt.x_mm) / 2 + nx * arrow.curve * dist
        my = (src.y_mm + tgt.y_mm) / 2 + ny * arrow.curve * dist
        segments = [(src.x_mm, src.y_mm, mx, my), (mx, my, tgt.x_mm, tgt.y_mm)]
    else:
        segments = [(src.x_mm, src.y_mm, tgt.x_mm, tgt.y_mm)]
    total_len = sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segments)
    occluded = 0.0
    for bid, pos in diagram._positions.items():
        if bid in (arrow.source, arrow.target) or bid not in diagram._boxes:
            continue
        bl, bb, br, bt = box_rect(pos)
        for x0, y0, x1, y1 in segments:
            occluded += seg_rect_clip_len(x0, y0, x1, y1, bl, bb, br, bt)
    return 1.0 - min(occluded / total_len, 1.0)


def fix_arrow_occlusion(diagram: "Diagram", min_visible: float = 0.9) -> int:
    """R7: Auto-curve arrows occluded by intermediate boxes.

    Tries curve values in both directions, picking the one with best
    visibility. Skips arrows where the user already set a curve.
    """
    fixed = 0
    for arrow in diagram._arrows:
        if arrow.curve != 0.0:
            continue
        vis = _arrow_visibility_prerender(diagram, arrow)
        if vis >= min_visible:
            continue
        best_curve, best_vis = 0.0, vis
        for c in [0.3, -0.3, 0.5, -0.5, 0.7, -0.7, 1.0, -1.0]:
            arrow.curve = c
            v = _arrow_visibility_prerender(diagram, arrow)
            if v > best_vis:
                best_curve, best_vis = c, v
            if v >= min_visible:
                break
        arrow.curve = best_curve
        if best_curve != 0.0:
            logger.warning(
                "  R7 occlusion: '%s'->'%s' vis=%.0f%% -> curved %.2f (%.0f%%)",
                arrow.source,
                arrow.target,
                vis * 100,
                best_curve,
                best_vis * 100,
            )
            fixed += 1
    return fixed


# ── Phase 2: Post-render fixers ─────────────────────────────────────


def _arrow_perp(diagram, arrow):
    """Return (nx, ny) perpendicular unit vector for an arrow."""
    src = diagram._positions.get(arrow.source)
    tgt = diagram._positions.get(arrow.target)
    if not src or not tgt:
        return (0, 1)
    dx = tgt.x_mm - src.x_mm
    dy = tgt.y_mm - src.y_mm
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return (0, 1)
    return (dy / dist, -dx / dist)


def fix_post_render(diagram, fig, ax, min_margin=2.0) -> int:
    """R5/R6/R7: Offset arrow labels to fix text collisions and occlusion.

    Detects two types of problems:
    - R5/R6: Arrow label too close to other text (gap < min_margin).
    - R7: Arrow label sitting on top of its own arrow path.

    Offsets affected labels perpendicular to the arrow direction.
    Returns number of arrow labels adjusted.
    """
    from ._geom import bbox_gap, box_rect, seg_rect_clip_len

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    # Collect all text bboxes
    text_entries = []
    for t in ax.texts:
        txt = t.get_text().strip()
        if not txt or t.get_label() == "__codeblock_internal__":
            continue
        bb = t.get_window_extent(renderer).transformed(inv)
        text_entries.append((txt, bb))

    arrow_labels = {a.label for a in diagram._arrows if a.label}

    fixed = 0
    for arrow in diagram._arrows:
        if not arrow.label:
            continue
        label_bb = None
        for txt, bb in text_entries:
            if txt == arrow.label:
                label_bb = bb
                break
        if label_bb is None:
            continue

        needs_fix = False

        # R7: Check if label bbox occludes the arrow path
        src = diagram._positions.get(arrow.source)
        tgt = diagram._positions.get(arrow.target)
        if src and tgt:
            clip = seg_rect_clip_len(
                src.x_mm,
                src.y_mm,
                tgt.x_mm,
                tgt.y_mm,
                label_bb.x0,
                label_bb.y0,
                label_bb.x1,
                label_bb.y1,
            )
            if clip > 0:
                needs_fix = True

        # R5/R6: Check collision with non-arrow-label text
        if not needs_fix:
            for txt, bb in text_entries:
                if txt == arrow.label or txt in arrow_labels:
                    continue
                if bbox_gap(label_bb, bb) < min_margin:
                    needs_fix = True
                    break

        # R5/R6: Check proximity to box/container edges
        if not needs_fix:
            from matplotlib.transforms import Bbox

            for eid in list(diagram._boxes) + list(diagram._containers):
                if eid not in diagram._positions:
                    continue
                el, eb, er, et = box_rect(diagram._positions[eid])
                cx = (label_bb.x0 + label_bb.x1) / 2
                cy = (label_bb.y0 + label_bb.y1) / 2
                if el <= cx <= er and eb <= cy <= et:
                    continue  # label inside this box
                edge_bb = Bbox([[el, eb], [er, et]])
                if bbox_gap(label_bb, edge_bb) < min_margin:
                    needs_fix = True
                    break

        if not needs_fix:
            continue

        # Offset label perpendicular to arrow direction
        nx, ny = _arrow_perp(diagram, arrow)
        base_offset = arrow.label_offset_mm or (0, 0)
        for offset_mm in (5, 8, 12, -5, -8, -12):
            arrow.label_offset_mm = (
                base_offset[0] + nx * offset_mm,
                base_offset[1] + ny * offset_mm,
            )
            logger.warning(
                "  R5/R6 post_render: '%s'->'%s' label='%s' offset %+.1fmm",
                arrow.source,
                arrow.target,
                arrow.label,
                offset_mm,
            )
            fixed += 1
            break  # Apply first offset; re-render will re-check

    return fixed
