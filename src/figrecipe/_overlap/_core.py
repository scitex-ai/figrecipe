#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Top-level entry point for figrecipe overlap detection.

:func:`run_overlap_audit` is invoked from the save path; it builds the
shared hitmap once, runs all three detectors, and applies the
configured policies (strict / warn / off).
"""

from __future__ import annotations

import warnings
from typing import List, Optional

from ._color import DEFAULT_DELTA_E_THRESHOLD, detect_color_overlaps
from ._errors import OverlapError
from ._hitmap import build_element_hitmap
from ._legend import check_legend_overlap, record_legend_position
from ._policy import (
    OverlapPolicy,
    PolicyLevel,
    resolve_policy,
)
from ._report import OverlapReport
from ._shape import detect_shape_overlaps


def detect_overlaps(
    fig,
    *,
    shape_policy: PolicyLevel = "strict",
    color_policy: PolicyLevel = "warn",
    legend_policy: PolicyLevel = "warn",
    color_threshold: float = DEFAULT_DELTA_E_THRESHOLD,
    hitmap_dpi: int = 150,
) -> OverlapReport:
    """Run all three detectors on ``fig`` and return a structured report.

    This is the *non-raising* form — callers (CLI ``figrecipe audit``,
    notebook ``fr.audit_overlap``) typically want the full report
    regardless of severity. The save path uses
    :func:`run_overlap_audit` instead, which honours per-figure and
    per-axes policy overrides.
    """
    report = OverlapReport()

    if shape_policy == "off" and color_policy == "off" and legend_policy == "off":
        return report

    need_hitmap = shape_policy != "off" or color_policy != "off"
    hitmap = None
    if need_hitmap:
        try:
            hitmap = build_element_hitmap(
                fig,
                dpi=hitmap_dpi,
                include_real_render=color_policy != "off",
            )
        except Exception as exc:
            warnings.warn(
                f"figrecipe overlap-detection: hitmap build failed ({exc}); "
                "skipping shape/color audit",
                UserWarning,
                stacklevel=2,
            )
            hitmap = None

    if hitmap is not None and shape_policy != "off":
        report.shape.extend(
            detect_shape_overlaps(
                hitmap, fig=fig, default_severity=_severity_for(shape_policy)
            )
        )

    if hitmap is not None and color_policy != "off":
        report.color.extend(
            detect_color_overlaps(
                hitmap,
                threshold=color_threshold,
                severity=_severity_for(color_policy),
            )
        )

    if legend_policy != "off":
        mpl_fig = getattr(fig, "_fig", fig)
        for ax in mpl_fig.get_axes():
            try:
                leg_report = check_legend_overlap(ax, fig=fig, policy=legend_policy)
            except OverlapError:
                raise
            if leg_report is not None:
                report.legend.append(leg_report)
                record_legend_position(fig, leg_report)

    return report


def _severity_for(policy: PolicyLevel) -> str:
    if policy == "strict":
        return "error"
    if policy == "warn":
        return "warn"
    return "off"


def run_overlap_audit(
    fig,
    *,
    color_threshold: float = DEFAULT_DELTA_E_THRESHOLD,
    hitmap_dpi: int = 150,
) -> OverlapReport:
    """Save-path entrypoint.

    Resolves per-figure / per-axes policy, builds the shared hitmap once,
    runs all detectors, then:

    * Raises :class:`OverlapError` on the first strict-error report.
    * Emits :class:`UserWarning` for each warn-level report.
    * Returns the report so the caller can stash it on the FigureRecord.
    """
    # Aggregate per-kind effective policy at figure scope (per-axes /
    # per-artist overrides are then applied inside each detector).
    shape_pol = resolve_policy(fig=fig, kind="shape")
    color_pol = resolve_policy(fig=fig, kind="color")
    legend_pol = resolve_policy(fig=fig, kind="legend")

    report = detect_overlaps(
        fig,
        shape_policy=shape_pol,
        color_policy=color_pol,
        legend_policy=legend_pol,
        color_threshold=color_threshold,
        hitmap_dpi=hitmap_dpi,
    )

    # Emit policy-driven side effects.
    _emit_or_raise(report)

    # Stash on the FigureRecord for downstream consumers.
    record = getattr(fig, "record", None) or getattr(fig, "_record", None)
    if record is not None:
        record._overlap_report = report.to_dict()

    return report


def _emit_or_raise(report: OverlapReport) -> None:
    # Errors first — strict policy raises immediately.
    errors = report.errors()
    if errors:
        first = errors[0]
        elements = [first.element_a, first.element_b]
        raise OverlapError(
            _format_message(first),
            elements=elements,
            axes_key=getattr(first, "axes_key", None),
            kind=getattr(first, "kind", None),
        )
    for item in report.warnings():
        warnings.warn(
            f"figrecipe overlap ({getattr(item, 'kind', '?')}): "
            + _format_message(item),
            UserWarning,
            stacklevel=3,
        )


def _format_message(item) -> str:
    parts = [
        f"{item.element_a} ↔ {item.element_b}",
    ]
    if getattr(item, "axes_key", None):
        parts.append(f"panel {item.axes_key}")
    kind = getattr(item, "kind", "")
    if kind == "color":
        parts.append(
            f"ΔE={item.delta_e:.2f} < {item.threshold} — {item.shared_color_summary}"
        )
    elif kind == "shape":
        parts.append(
            f"{item.overlap_pixels}px shared "
            f"({item.overlap_fraction * 100:.2f}% of figure)"
        )
    elif kind == "legend":
        if item.fallback_applied:
            parts.append(
                f"legend moved to {item.final_loc}@{item.final_bbox_to_anchor}"
            )
    return " — ".join(parts)


__all__ = ["detect_overlaps", "run_overlap_audit"]
