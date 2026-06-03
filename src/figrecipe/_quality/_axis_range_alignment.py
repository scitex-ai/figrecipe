#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime validator: ``axis_range_alignment``.

Complements the static ``STX-FIG001`` lint rule (which catches explicit
literal ``ax.set_ylim(0, 1)`` vs ``ax.set_ylim(0, 5)`` mismatches in
source). Most real matplotlib code uses autoscale or variable limits —
the displayed range only exists at runtime. This validator inspects
the actual rendered ``fig.axes`` at savefig time and warns when axes
that appear to plot the *same* quantity have mismatched displayed
ranges.

Rule reference: scientific-figure standards rule #4 — "Same axis
range on x and y, even if one condition has less data — the visual
comparison is destroyed by mismatched ranges".

Severity: WARNING by default — per the operator's preference
(figrecipe issue #134) the validator never raises after the PNG has
already been written. The caller may upgrade the severity via the
existing ``validate_error_level`` knob in ``save_figure``.

Opt-out: set ``fig._figrecipe_allow_axis_mismatch = True`` to skip.
"""

from __future__ import annotations

import math
import warnings
from typing import Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "AxisAlignmentResult",
    "check_axis_range_alignment",
    "WARNING_MESSAGE",
]


WARNING_MESSAGE = (
    "figrecipe.axis_range_alignment: subplots that appear to share a "
    "quantity (matching {xlabel|ylabel} or same gridspec {row|col}) "
    "have mismatched displayed ranges. This destroys visual comparison "
    "(scientific-figure standards rule #4)."
)


# Axis kind tags — internal to grouping.
_X_AXIS = "x"
_Y_AXIS = "y"


class AxisAlignmentResult:
    """Result of the ``axis_range_alignment`` runtime check.

    Attributes
    ----------
    triggered : bool
        True if at least one peer group has mismatched displayed
        ranges.
    message : str
        Human-readable explanation (constant ``WARNING_MESSAGE`` when
        triggered, empty string otherwise).
    mismatches : list of dict
        One entry per offending peer group. Each entry has keys
        ``axis`` ("x" or "y"), ``key`` (the grouping key — label
        string or gridspec row/col index), and ``ranges`` (list of
        (low, high) tuples in axis-iteration order).
    """

    __slots__ = ("triggered", "message", "mismatches")

    def __init__(
        self,
        triggered: bool,
        message: str = "",
        mismatches: Optional[List[dict]] = None,
    ) -> None:
        self.triggered = triggered
        self.message = message
        self.mismatches = list(mismatches) if mismatches else []

    def __repr__(self) -> str:  # pragma: no cover — trivial
        status = "MISMATCH" if self.triggered else "OK"
        return f"AxisAlignmentResult({status}, " f"groups={len(self.mismatches)})"


# ---------------------------------------------------------------------------
# Tolerance comparison
# ---------------------------------------------------------------------------


def _limits_close(
    a: Tuple[float, float],
    b: Tuple[float, float],
    rel_tol: float = 1e-3,
    abs_tol: float = 1e-9,
) -> bool:
    """Return True if both endpoints of (low, high) tuples match within
    tolerance, per the spec (``math.isclose(rel_tol=1e-3, abs_tol=1e-9)``).
    """
    return math.isclose(a[0], b[0], rel_tol=rel_tol, abs_tol=abs_tol) and math.isclose(
        a[1], b[1], rel_tol=rel_tol, abs_tol=abs_tol
    )


def _all_limits_close(limits: Sequence[Tuple[float, float]]) -> bool:
    """Return True if every (low, high) limit matches the first within
    tolerance.
    """
    if len(limits) < 2:
        return True
    pivot = limits[0]
    return all(_limits_close(pivot, lim) for lim in limits[1:])


# ---------------------------------------------------------------------------
# Per-axis skip predicates (be conservative)
# ---------------------------------------------------------------------------


def _is_twin_axis(ax) -> bool:
    """True if ``ax`` is a twin axis (``twinx`` / ``twiny``).

    Twins share one axis (x or y) AND occupy the same bounding box as
    their parent. Across matplotlib versions the ``_twinned_axes``
    registry on the parent figure may or may not be populated, so we
    fall back to the geometric/sibling test:

    1. ``ax`` shares either its x- or y-axis with at least one peer.
    2. That peer has an identical ``get_position()`` bbox — meaning
       both axes overlay the same physical region, which is the
       defining property of a twin.
    """
    fig = ax.figure

    # First try the modern registry (when present).
    twinned = getattr(fig, "_twinned_axes", None)
    if twinned is not None:
        try:
            siblings = list(twinned.get_siblings(ax))
            if len(siblings) > 1:
                return True
        except Exception:
            pass

    # Fallback: geometric / sibling overlap test. Robust across
    # matplotlib >= 3.4 (Grouper API) and >= 3.10 (registry absent).
    try:
        my_bbox = tuple(ax.get_position().bounds)
    except Exception:
        return False

    def _shared_siblings(getter_name: str):
        try:
            return list(getattr(ax, getter_name)().get_siblings(ax))
        except Exception:
            return [ax]

    for getter in ("get_shared_x_axes", "get_shared_y_axes"):
        for peer in _shared_siblings(getter):
            if peer is ax:
                continue
            try:
                peer_bbox = tuple(peer.get_position().bounds)
            except Exception:
                continue
            if all(
                math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
                for a, b in zip(my_bbox, peer_bbox)
            ):
                return True
    return False


def _is_non_rect_projection(ax) -> bool:
    """True for 3D / polar / non-rectilinear projections — skip them.

    These cannot reasonably be compared by ``get_xlim``/``get_ylim``
    tuples against rectilinear peers.
    """
    name = getattr(ax, "name", "rectilinear")
    if name and name != "rectilinear":
        return True
    # 3D check (mpl_toolkits.mplot3d sets name="3d" but defend anyway)
    if hasattr(ax, "get_zlim"):
        return True
    return False


def _has_shared_x(ax) -> bool:
    """True if matplotlib already shares the x-axis with any sibling."""
    try:
        siblings = list(ax.get_shared_x_axes().get_siblings(ax))
    except Exception:
        return False
    return len(siblings) > 1


def _has_shared_y(ax) -> bool:
    """True if matplotlib already shares the y-axis with any sibling."""
    try:
        siblings = list(ax.get_shared_y_axes().get_siblings(ax))
    except Exception:
        return False
    return len(siblings) > 1


def _gridspec_row_col(ax) -> Tuple[Optional[int], Optional[int]]:
    """Return (row, col) start indices from the SubplotSpec, or
    (None, None) if the axis was not placed via gridspec.
    """
    get_spec = getattr(ax, "get_subplotspec", None)
    if get_spec is None:
        return None, None
    try:
        spec = get_spec()
    except Exception:
        return None, None
    if spec is None:
        return None, None
    try:
        row_start, _row_stop, col_start, _col_stop = (
            spec.rowspan.start,
            spec.rowspan.stop,
            spec.colspan.start,
            spec.colspan.stop,
        )
    except AttributeError:
        return None, None
    return row_start, col_start


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------


def _eligible(ax, axis_kind: str) -> bool:
    """Return True if ``ax`` should participate in the comparison for
    the given axis_kind ("x" or "y").

    Conservative skips:
      - twin axes (twinx/twiny deliberately differ),
      - non-rectilinear projections (3D, polar, …),
      - axes whose matching matplotlib-side sharex/sharey is already on
        (mismatch impossible by construction).
    """
    if _is_twin_axis(ax):
        return False
    if _is_non_rect_projection(ax):
        return False
    if axis_kind == _X_AXIS and _has_shared_x(ax):
        return False
    if axis_kind == _Y_AXIS and _has_shared_y(ax):
        return False
    return True


def _group_by_label(axes: Iterable, axis_kind: str) -> dict:
    """Group axes by non-empty x/y label."""
    groups: dict = {}
    for ax in axes:
        if not _eligible(ax, axis_kind):
            continue
        label = ax.get_xlabel() if axis_kind == _X_AXIS else ax.get_ylabel()
        if not label:
            continue
        groups.setdefault(label, []).append(ax)
    return groups


def _group_by_gridspec(axes: Iterable, axis_kind: str) -> dict:
    """Group axes by gridspec row (x-axis quantity peer group) or
    column (y-axis quantity peer group).

    Convention (matches matplotlib ``sharex='row'`` / ``sharey='col'``):

    * Axes sharing the same row → candidates for shared x-quantity.
    * Axes sharing the same column → candidates for shared y-quantity.

    Only emit a group if the gridspec has more than one row (for x) or
    more than one column (for y); otherwise the grouping degenerates
    into "all axes" and conflicts with label-based grouping.
    """
    rows_cols: List[Tuple[int, int, object]] = []
    for ax in axes:
        if not _eligible(ax, axis_kind):
            continue
        row, col = _gridspec_row_col(ax)
        if row is None or col is None:
            continue
        rows_cols.append((row, col, ax))

    if not rows_cols:
        return {}

    distinct_rows = {r for r, _, _ in rows_cols}
    distinct_cols = {c for _, c, _ in rows_cols}

    groups: dict = {}
    if axis_kind == _X_AXIS:
        if len(distinct_rows) <= 1:
            return {}
        for row, _col, ax in rows_cols:
            groups.setdefault(row, []).append(ax)
    else:  # _Y_AXIS
        if len(distinct_cols) <= 1:
            return {}
        for _row, col, ax in rows_cols:
            groups.setdefault(col, []).append(ax)
    return groups


# ---------------------------------------------------------------------------
# Public check
# ---------------------------------------------------------------------------


def _opted_out(fig) -> bool:
    """Honor the per-figure opt-out sentinel."""
    return bool(getattr(fig, "_figrecipe_allow_axis_mismatch", False))


def _has_any_inferable_peer(ax) -> bool:
    """True if at least one signal (xlabel, ylabel, gridspec) lets us
    place this axis into a peer group. Used only to decide whether to
    skip an axis when it carries no information at all.
    """
    if ax.get_xlabel() or ax.get_ylabel():
        return True
    row, col = _gridspec_row_col(ax)
    return row is not None and col is not None


def _collect_mismatches(fig, axis_kind: str) -> List[dict]:
    """Return one mismatch record per offending peer group along the
    given axis.
    """
    axes = [ax for ax in fig.axes if _has_any_inferable_peer(ax)]
    if len(axes) < 2:
        return []

    mismatches: List[dict] = []
    seen_pairs = set()

    label_groups = _group_by_label(axes, axis_kind)
    gridspec_groups = _group_by_gridspec(axes, axis_kind)

    def _emit(key, group_axes):
        if len(group_axes) < 2:
            return
        getter = "get_xlim" if axis_kind == _X_AXIS else "get_ylim"
        limits = [tuple(getattr(a, getter)()) for a in group_axes]
        if _all_limits_close(limits):
            return
        ax_ids = tuple(sorted(id(a) for a in group_axes))
        pair_key = (axis_kind, ax_ids)
        if pair_key in seen_pairs:
            return
        seen_pairs.add(pair_key)
        mismatches.append({"axis": axis_kind, "key": key, "ranges": limits})

    for key, group in label_groups.items():
        _emit(key, group)
    for key, group in gridspec_groups.items():
        _emit(key, group)
    return mismatches


def check_axis_range_alignment(fig) -> AxisAlignmentResult:
    """Runtime check that axes plotting the same quantity share their
    displayed range.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The fully-rendered figure (after all plotting / autoscale).
        ``RecordingFigure`` callers should pass ``fig.fig`` (the
        underlying matplotlib ``Figure``).

    Returns
    -------
    AxisAlignmentResult
        ``triggered=False`` when no mismatches are detected, when the
        check is opted out, or when fewer than two axes are present.
    """
    if fig is None:
        return AxisAlignmentResult(False)
    if _opted_out(fig):
        return AxisAlignmentResult(False)

    axes = list(getattr(fig, "axes", []) or [])
    if len(axes) < 2:
        return AxisAlignmentResult(False)

    mismatches: List[dict] = []
    mismatches.extend(_collect_mismatches(fig, _X_AXIS))
    mismatches.extend(_collect_mismatches(fig, _Y_AXIS))

    if not mismatches:
        return AxisAlignmentResult(False)

    return AxisAlignmentResult(
        triggered=True,
        message=WARNING_MESSAGE,
        mismatches=mismatches,
    )


def run_axis_range_alignment(
    fig,
    validate_error_level: str = "warning",
) -> AxisAlignmentResult:
    """Run the check and dispatch the result according to
    ``validate_error_level``.

    Defaults to ``"warning"`` per the operator preference (figrecipe
    issue #134): never kill the script after the PNG has already been
    written. Callers can opt up to ``"error"`` or down to ``"debug"``.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure to inspect.
    validate_error_level : {"warning", "error", "debug"}
        Dispatch level. ``"warning"`` emits ``warnings.warn`` (default),
        ``"error"`` raises ``ValueError``, ``"debug"`` is silent.
    """
    result = check_axis_range_alignment(fig)
    if not result.triggered:
        return result

    level = (validate_error_level or "warning").lower()
    if level == "error":
        raise ValueError(result.message)
    if level == "warning":
        warnings.warn(result.message, UserWarning, stacklevel=2)
    # "debug" → silent
    return result


# EOF
