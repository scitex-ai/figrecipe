#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout validation for Diagram diagrams.

Rules (all enforced programmatically):
  R1  Container must enclose all children          → ValueError
  R2  No two boxes may overlap                     → ValueError
  R3  Container title must clear children (5mm)    → UserWarning
  R4  Box text must fit within padded inner area    → UserWarning
  R5  Text-to-text margin >= MIN_MARGIN_MM          → ValueError
  R6  Text-to-edge margin >= MIN_MARGIN_MM          → ValueError
  R7  Arrow visible-length ratio >= MIN_VISIBLE     → ValueError
  R8  Curved-arrow label on same side as arc        → ValueError
  R9  All elements within canvas bounds              → ValueError
"""

from typing import TYPE_CHECKING

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

from ._geom import bbox_gap, box_rect, rects_overlap, seg_rect_clip_len

# Centralised thresholds
MIN_MARGIN_MM = 2.0  # R5, R6
MIN_VISIBLE = 0.9  # R7

if TYPE_CHECKING:
    from ._core import Diagram


def validate_containers(diagram: "Diagram") -> None:
    """Check that every container fully encloses its declared children.

    Parameters
    ----------
    diagram : Diagram
        The diagram to validate.

    Raises
    ------
    ValueError
        If any child box extends outside its parent container.
    """
    for cid, container in diagram._containers.items():
        if cid not in diagram._positions:
            continue
        cpos = diagram._positions[cid]
        c_left = cpos.x_mm - cpos.width_mm / 2
        c_right = cpos.x_mm + cpos.width_mm / 2
        c_bottom = cpos.y_mm - cpos.height_mm / 2
        c_top = cpos.y_mm + cpos.height_mm / 2

        for child_id in container.get("children", []):
            if child_id not in diagram._positions:
                continue
            chpos = diagram._positions[child_id]
            ch_left = chpos.x_mm - chpos.width_mm / 2
            ch_right = chpos.x_mm + chpos.width_mm / 2
            ch_bottom = chpos.y_mm - chpos.height_mm / 2
            ch_top = chpos.y_mm + chpos.height_mm / 2

            violations = []
            if ch_left < c_left:
                violations.append(
                    f"left edge ({ch_left:.1f}) < container left ({c_left:.1f})"
                )
            if ch_right > c_right:
                violations.append(
                    f"right edge ({ch_right:.1f}) > container right ({c_right:.1f})"
                )
            if ch_bottom < c_bottom:
                violations.append(
                    f"bottom edge ({ch_bottom:.1f}) < container bottom ({c_bottom:.1f})"
                )
            if ch_top > c_top:
                violations.append(
                    f"top edge ({ch_top:.1f}) > container top ({c_top:.1f})"
                )

            if violations:
                raise ValueError(
                    f"Child '{child_id}' extends outside container "
                    f"'{cid}': " + "; ".join(violations)
                )


def validate_no_overlap(diagram: "Diagram") -> None:
    """Check that no two boxes overlap each other.

    Containers are excluded — only boxes are checked.
    """
    from itertools import combinations

    box_ids = [bid for bid in diagram._boxes if bid in diagram._positions]
    for id_a, id_b in combinations(box_ids, 2):
        r_a = box_rect(diagram._positions[id_a])
        r_b = box_rect(diagram._positions[id_b])
        if rects_overlap(r_a, r_b):
            raise ValueError(
                f"Boxes '{id_a}' and '{id_b}' overlap: "
                f"'{id_a}' rect=({r_a[0]:.1f},{r_a[1]:.1f})-"
                f"({r_a[2]:.1f},{r_a[3]:.1f}), "
                f"'{id_b}' rect=({r_b[0]:.1f},{r_b[1]:.1f})-"
                f"({r_b[2]:.1f},{r_b[3]:.1f})"
            )


def validate_text_margins(fig, ax, diagram, min_margin_mm=MIN_MARGIN_MM) -> None:
    """Check all text has minimum margin from other text and box edges.

    Raises ValueError if text-to-text or text-to-edge gap < min_margin_mm.
    Arrows are excluded (accepted by design).
    Must be called after render.
    """
    from itertools import combinations

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    texts = [
        t
        for t in ax.texts
        if t.get_text().strip() and t.get_label() != "__codeblock_internal__"
    ]
    if not texts:
        return

    # Build box rects for ownership lookup
    box_rects = {}
    for eid in list(diagram._boxes) + list(diagram._containers):
        if eid in diagram._positions:
            box_rects[eid] = box_rect(diagram._positions[eid])

    def _owner(bb):
        """Return the box/container ID whose rect contains bb center."""
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        for eid, (el, eb, er, et) in box_rects.items():
            if el <= cx <= er and eb <= cy <= et and eid in diagram._boxes:
                return eid
        return None

    entries = []
    for t in texts:
        bb = t.get_window_extent(renderer).transformed(ax.transData.inverted())
        entries.append((t.get_text(), bb, _owner(bb)))

    # 1. Text-to-text margin check (skip pairs in same box)
    for (txt_a, bb_a, own_a), (txt_b, bb_b, own_b) in combinations(entries, 2):
        if own_a is not None and own_a == own_b:
            continue
        gap = bbox_gap(bb_a, bb_b)
        if gap < min_margin_mm:
            raise ValueError(
                f"Text margin violation: '{txt_a}' and '{txt_b}' "
                f"gap={gap:.1f}mm (min={min_margin_mm}mm)"
            )

    # 2. Text-to-box/container-edge margin check
    edges = []
    for eid in list(diagram._boxes) + list(diagram._containers):
        if eid in diagram._positions:
            edges.append((eid, box_rect(diagram._positions[eid])))

    for txt, bb, _own in entries:
        for eid, (el, eb, er, et) in edges:
            # Skip if text center is inside this box (it belongs there)
            cx = (bb.x0 + bb.x1) / 2
            cy = (bb.y0 + bb.y1) / 2
            if el <= cx <= er and eb <= cy <= et:
                continue
            # Check gap to this edge rect
            from matplotlib.transforms import Bbox

            edge_bb = Bbox([[el, eb], [er, et]])
            gap = bbox_gap(bb, edge_bb)
            if gap < min_margin_mm:
                raise ValueError(
                    f"Text '{txt}' too close to '{eid}' edge: "
                    f"gap={gap:.1f}mm (min={min_margin_mm}mm)"
                )


def validate_text_no_overlap(fig, ax, min_overlap_ratio=0.05) -> None:
    pass  # Superseded by validate_text_margins


def validate_container_title_clearance(
    diagram: "Diagram", min_gap_mm: float = 3.0
) -> None:
    """Warn if container title area overlaps with children.

    The title occupies approximately 5mm from the container top edge.
    Children whose top edge is within this zone get a warning.
    """

    _TITLE_ZONE_MM = 5.0  # approximate height of title text region

    for cid, container in diagram._containers.items():
        if cid not in diagram._positions or not container.get("title"):
            continue
        cpos = diagram._positions[cid]
        c_top = cpos.y_mm + cpos.height_mm / 2
        title_bottom = c_top - _TITLE_ZONE_MM

        for child_id in container.get("children", []):
            if child_id not in diagram._positions:
                continue
            chpos = diagram._positions[child_id]
            ch_top = chpos.y_mm + chpos.height_mm / 2
            gap = title_bottom - ch_top
            if gap < min_gap_mm:
                logger.warning(
                    f"Container '{cid}' title too close to child "
                    f"'{child_id}': gap={gap:.1f}mm (min={min_gap_mm}mm). "
                    f"Increase container height or lower child."
                )


def validate_text_fits_boxes(diagram: "Diagram") -> None:
    """Warn if a box has more text lines than fit within its padded area.

    Estimates text height from font sizes (1pt ≈ 0.35mm) and checks
    against the box inner height (height - 2*padding).
    """
    _PT_TO_MM = 0.35  # approximate pt → mm conversion

    for bid, box in diagram._boxes.items():
        if bid not in diagram._positions:
            continue
        pos = diagram._positions[bid]
        inner_h = pos.height_mm - 2 * box.padding_mm

        # Estimate total text height
        text_h = 11 * _PT_TO_MM  # title always present
        if box.subtitle:
            text_h += 9 * _PT_TO_MM
        text_h += len(box.content) * 8 * _PT_TO_MM

        if text_h > inner_h:
            logger.warning(
                f"Box '{bid}' text (~{text_h:.1f}mm) exceeds "
                f"inner height ({inner_h:.1f}mm). "
                f"Increase box height or reduce content."
            )


def validate_text_arrow_no_overlap(fig, ax, diagram=None, min_visible=MIN_VISIBLE):
    """Raise if arrow visible-length ratio drops below min_visible.

    Flattens each arrow's Bezier curve into line segments, measures
    total arc length, and subtracts the length occluded by text bboxes
    AND intermediate box rectangles (excluding source/target boxes).
    """
    import math

    from matplotlib.patches import FancyArrowPatch

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    texts = [t for t in ax.texts if t.get_text().strip()]
    arrows = [p for p in ax.patches if isinstance(p, FancyArrowPatch)]
    if not arrows:
        return

    arrow_specs = []
    if diagram is not None:
        arrow_specs = list(diagram._arrows)

    text_bbs = []
    for t in texts:
        bb = t.get_window_extent(renderer).transformed(inv)
        text_bbs.append((t.get_text(), bb))

    # Build box rects in data coords for intermediate-box occlusion
    box_rects = {}
    if diagram is not None:
        for bid in diagram._boxes:
            if bid in diagram._positions:
                box_rects[bid] = box_rect(diagram._positions[bid])

    for i, arrow in enumerate(arrows):
        aspec = arrow_specs[i] if i < len(arrow_specs) else None
        aid = (
            aspec.id
            if aspec and aspec.id
            else f"{aspec.source}->{aspec.target}"
            if aspec
            else f"arrow#{i}"
        )
        src_id = aspec.source if aspec else None
        tgt_id = aspec.target if aspec else None
        # Flatten Bezier curves into dense polygon points
        disp_path = arrow.get_path().transformed(arrow.get_transform())
        polys = disp_path.to_polygons(closed_only=False)
        if not polys:
            continue
        # Transform polygon points to data coords
        pts_disp = polys[0]
        pts = inv.transform(pts_disp)
        if len(pts) < 2:
            continue
        # Measure total length and occluded length per segment
        total_len = 0.0
        occluded_len = 0.0
        occluders = set()
        for j in range(len(pts) - 1):
            x0, y0 = pts[j]
            x1, y1 = pts[j + 1]
            seg_len = math.hypot(x1 - x0, y1 - y0)
            total_len += seg_len
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            occluded = False
            # Check text bboxes
            for txt, bb in text_bbs:
                if bb.x0 <= mx <= bb.x1 and bb.y0 <= my <= bb.y1:
                    occluded_len += seg_len
                    occluders.add(f"text:'{txt}'")
                    occluded = True
                    break
            if occluded:
                continue
            # Check intermediate box rectangles (line-rect clipping)
            for bid, (bl, bb_, br, bt) in box_rects.items():
                if bid == src_id or bid == tgt_id:
                    continue
                clip = seg_rect_clip_len(x0, y0, x1, y1, bl, bb_, br, bt)
                if clip > 0:
                    occluded_len += clip
                    occluders.add(f"box:'{bid}'")
        if total_len < 1e-6:
            continue
        visible_ratio = 1.0 - occluded_len / total_len
        if visible_ratio < min_visible:
            occ_str = ", ".join(sorted(occluders))
            raise ValueError(
                f"'{aid}' visibility {visible_ratio:.0%} < {min_visible:.0%}. "
                f"Occluded by: {occ_str}"
            )


def validate_arrow_label_side(diagram: "Diagram") -> None:
    """R8: Curved-arrow label must be on same side as arc bulge.

    For each arrow with curve != 0 and a label, checks that the final
    label position is on the same side of the straight line as the arc.
    """
    import math

    for arrow in diagram._arrows:
        if not arrow.curve or not arrow.label:
            continue
        src_pos = diagram._positions.get(arrow.source)
        tgt_pos = diagram._positions.get(arrow.target)
        if not src_pos or not tgt_pos:
            continue
        # Resolve anchors
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
        # Arc side: perpendicular of (start→end), scaled by curve sign
        dx, dy = end[0] - start[0], end[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            continue
        nx, ny = dy / dist, -dx / dist  # same as in compute_arrow_label_position
        arc_side = nx * arrow.curve, ny * arrow.curve  # direction of bulge
        # Label offset from straight-line midpoint
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        label_off = (lx - mx, ly - my)
        # Dot product: positive means same side
        dot = label_off[0] * arc_side[0] + label_off[1] * arc_side[1]
        if dot < 0:
            aid = arrow.id or f"{arrow.source}->{arrow.target}"
            raise ValueError(
                f"R8: '{aid}' label '{arrow.label}' is on the wrong side "
                f"of the arc. Flip curve sign or adjust label_offset_mm."
            )


def compute_arrow_label_position(start, end, curve, label_offset_mm=None):
    """Compute label position for an arrow, accounting for curve.

    For curved arrows (arc3), the label is placed at the curve's peak
    rather than the straight-line midpoint.

    Returns (x_mm, y_mm) for the label center.
    """
    import math

    mx = (start[0] + end[0]) / 2
    my = (start[1] + end[1]) / 2

    if curve:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            # Perpendicular matching arc3: control = mid + rad*(dy, -dx)
            nx, ny = dy / dist, -dx / dist
            # arc3 peak deviation ≈ rad * dist * 0.5
            mx += nx * curve * dist * 0.5
            my += ny * curve * dist * 0.5

    # No base offset — label centered at arrow midpoint

    # Manual override
    if label_offset_mm:
        mx += label_offset_mm[0]
        my += label_offset_mm[1]

    return mx, my


def validate_canvas_bounds(diagram: "Diagram") -> None:
    """R9: Check that all boxes and containers are within canvas bounds.

    Uses xlim/ylim (which may differ from 0..width/height after auto-layout
    or auto-height).
    """
    x_lo, x_hi = diagram.xlim
    y_lo, y_hi = diagram.ylim
    all_ids = list(diagram._boxes) + list(diagram._containers)
    for eid in all_ids:
        if eid not in diagram._positions:
            continue
        left, bottom, right, top = box_rect(diagram._positions[eid])
        violations = []
        if left < x_lo:
            violations.append(f"left={left:.1f}mm < xlim_lo={x_lo:.1f}mm")
        if bottom < y_lo:
            violations.append(f"bottom={bottom:.1f}mm < ylim_lo={y_lo:.1f}mm")
        if right > x_hi:
            violations.append(f"right={right:.1f}mm > xlim_hi={x_hi:.1f}mm")
        if top > y_hi:
            violations.append(f"top={top:.1f}mm > ylim_hi={y_hi:.1f}mm")
        if violations:
            raise ValueError(f"'{eid}' extends outside canvas: {'; '.join(violations)}")


def validate_all(diagram, fig=None, ax=None):
    """Run all validation rules, collect errors, raise combined summary.

    Pre-render rules (R1-R4, R8) always run. Post-render rules (R5-R7)
    only run when fig and ax are provided.
    """
    errors = []

    # Pre-render rules
    pre_checks = [
        ("R1", validate_containers),
        ("R2", validate_no_overlap),
        ("R8", validate_arrow_label_side),
        ("R9", validate_canvas_bounds),
    ]
    for tag, fn in pre_checks:
        try:
            fn(diagram)
        except ValueError as e:
            errors.append(f"{tag}: {e}")

    # Warning-level pre-render (R3, R4) — run but don't collect
    validate_container_title_clearance(diagram)
    validate_text_fits_boxes(diagram)

    # Post-render rules (need fig/ax with rendered text)
    if fig is not None and ax is not None:
        post_checks = [
            ("R5/R6", validate_text_margins),
            ("R7", validate_text_arrow_no_overlap),
        ]
        for tag, fn in post_checks:
            try:
                if "diagram" in fn.__code__.co_varnames:
                    fn(fig, ax, diagram)
                else:
                    fn(fig, ax)
            except ValueError as e:
                errors.append(f"{tag}: {e}")

    if errors:
        n = len(errors)
        detail = "\n  ".join(errors)
        raise ValueError(f"{n} validation error(s):\n  {detail}")


# EOF
