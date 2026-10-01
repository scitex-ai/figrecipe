#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report text whose rendered font size disagrees with the active style.

Operator request via neurovista, 2026-06-28: flag "any element whose font size
deviates from the SCITEX expected sizes ... i.e. detect inconsistent fonts across
panels (the same class of bug as the PIL-tiler font distortion and the panel-label
size bug fixed in 0.29.8)".

EXPECTED SIZES ARE READ FROM THE STYLE, NEVER RESTATED HERE, and that is the
load-bearing decision. The request quotes "axis label 7 / legend 6 / tick 6 /
title 8", but the shipped style resolves ``tick_label_pt: 7`` — measured
2026-08-09. A checker hardcoding the quoted list would report EVERY correctly
styled figure's tick labels as wrong, on the most numerous text element in any
figure, and a check that cries wolf on correct input is worse than no check.
Reading ``get_style()["fonts"]`` makes this correct by construction and unable to
drift from the renderer, whatever the style says today.

Same discipline as ``_compose_whitespace``, which derives whitespace from
``layout_report`` rather than re-measuring geometry: one question, one answer.

ROLES ARE ASKED FOR, NOT GUESSED. matplotlib exposes each piece of text
explicitly — ``ax.xaxis.label``, ``ax.get_xticklabels()``, ``ax.title``, the
legend's texts — so nothing here infers a role from position or content. A
heuristic would mislabel elements and produce exactly the false positives this
module is written to avoid.

REPORT ONLY BY DEFAULT. ``check_font_consistency`` raises solely when a caller
passes ``strict=True``; promoting figure violations to hard errors across the
ecosystem is one coordinated decision, tracked alongside the overlap-severity and
whitespace-default questions, not something to switch on per-module.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional

#: Rendered vs expected difference, in points, below which nothing is reported.
#: matplotlib stores sizes as floats and a style may carry a fractional value, so
#: an exact-equality check would flag rounding rather than a real mismatch.
TOLERANCE_PT = 0.01

#: Which style key states the expected size for each role we can identify.
#: A role whose key is absent from the style is reported as UNKNOWN, never
#: silently skipped and never defaulted to a number invented here.
ROLE_STYLE_KEY = {
    "axis_label": "axis_label_pt",
    "tick_label": "tick_label_pt",
    "title": "title_pt",
    "legend": "legend_pt",
    "suptitle": "suptitle_pt",
    "supxlabel": "supxlabel_pt",
    "supylabel": "supylabel_pt",
    "panel_label": "panel_label_pt",
}


def _style_font_sizes() -> Optional[Dict[str, float]]:
    """The active style's font block, or None if it cannot be read."""
    try:
        from ..styles._style_loader import get_style

        style = get_style()
    except Exception:  # pragma: no cover - never break a figure over a metric
        return None
    if style is None:
        return None
    try:
        fonts = style.get("fonts", None) if hasattr(style, "get") else None
        if fonts is None:
            fonts = getattr(style, "fonts", None)
    except (KeyError, AttributeError):
        return None
    if fonts is None:
        return None
    try:
        return {str(k): v for k, v in dict(fonts).items()}
    except Exception:  # pragma: no cover
        return None


def _rendered_text(fig: Any) -> List[Dict[str, Any]]:
    """Every text element we can name a ROLE for, with its rendered size.

    Only elements matplotlib hands us by role are included. Free ``fig.text``
    calls are deliberately excluded: their role is genuinely unknown, and
    guessing would manufacture the false positives this module avoids.
    """
    raw = getattr(fig, "fig", fig)
    items: List[Dict[str, Any]] = []

    for idx, ax in enumerate(getattr(raw, "axes", []) or []):
        where = f"axes[{idx}]"
        for role, obj in (
            ("axis_label", getattr(getattr(ax, "xaxis", None), "label", None)),
            ("axis_label", getattr(getattr(ax, "yaxis", None), "label", None)),
            ("title", getattr(ax, "title", None)),
        ):
            if obj is not None and (obj.get_text() or "").strip():
                items.append(
                    {"role": role, "where": where, "size_pt": obj.get_fontsize()}
                )
        for getter in ("get_xticklabels", "get_yticklabels"):
            try:
                labels = getattr(ax, getter)()
            except Exception:  # pragma: no cover
                continue
            for lab in labels:
                if (lab.get_text() or "").strip():
                    items.append(
                        {
                            "role": "tick_label",
                            "where": where,
                            "size_pt": lab.get_fontsize(),
                        }
                    )
        legend = ax.get_legend() if hasattr(ax, "get_legend") else None
        if legend is not None:
            for txt in getattr(legend, "texts", []) or []:
                items.append(
                    {"role": "legend", "where": where, "size_pt": txt.get_fontsize()}
                )

    for attr, role in (
        ("_suptitle", "suptitle"),
        ("_supxlabel", "supxlabel"),
        ("_supylabel", "supylabel"),
    ):
        obj = getattr(raw, attr, None)
        if obj is not None and (obj.get_text() or "").strip():
            items.append({"role": role, "where": "figure", "size_pt": obj.get_fontsize()})

    return items


def font_consistency(fig: Any) -> Optional[Dict[str, Any]]:
    """Compare every named text element's size against the style.

    Returns ``{"checked", "deviations", "unknown_roles"}``, or None when the
    style's font block cannot be read — reported as unknown rather than as
    "nothing wrong", which is the failure mode that makes a check useless.

    ``deviations`` entries carry role, location, expected and actual, so the
    message names the offending value rather than only asserting a problem.
    """
    fonts = _style_font_sizes()
    if fonts is None:
        return None

    deviations: List[Dict[str, Any]] = []
    unknown_roles: List[str] = []
    checked = 0

    for item in _rendered_text(fig):
        key = ROLE_STYLE_KEY.get(item["role"])
        expected = fonts.get(key) if key else None
        if expected is None:
            if item["role"] not in unknown_roles:
                unknown_roles.append(item["role"])
            continue
        checked += 1
        actual = item["size_pt"]
        if actual is None:
            continue
        if abs(float(actual) - float(expected)) > TOLERANCE_PT:
            deviations.append(
                {
                    "role": item["role"],
                    "where": item["where"],
                    "expected_pt": float(expected),
                    "actual_pt": float(actual),
                }
            )

    return {
        "checked": checked,
        "deviations": deviations,
        "unknown_roles": unknown_roles,
    }


def check_font_consistency(fig: Any, strict: bool = False) -> Optional[Dict[str, Any]]:
    """Report font-size deviations; raise only when ``strict``.

    Returns the same payload as ``font_consistency``. With ``strict=True`` a
    non-empty ``deviations`` list raises ValueError naming each offender.
    """
    report = font_consistency(fig)
    if report is None or not report["deviations"]:
        return report

    lines = [
        f"  {d['role']} in {d['where']}: {d['actual_pt']}pt, style says "
        f"{d['expected_pt']}pt"
        for d in report["deviations"][:8]
    ]
    more = len(report["deviations"]) - len(lines)
    if more > 0:
        lines.append(f"  (+{more} more)")

    detail = "\n".join(lines)
    message = (
        f"figrecipe: {len(report['deviations'])} text element(s) do not match the "
        f"active style's font sizes:\n{detail}\n"
        "Inconsistent sizes across panels are invisible on screen and obvious in "
        "print. Set sizes via the style rather than per-call kwargs, or pass "
        "strict=False to report without failing."
    )
    if strict:
        raise ValueError(message)
    warnings.warn(message, UserWarning, stacklevel=2)
    return report


__all__ = [
    "ROLE_STYLE_KEY",
    "TOLERANCE_PT",
    "check_font_consistency",
    "font_consistency",
]

# EOF
