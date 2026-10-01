#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Measure — and optionally refuse — a composite that is mostly blank.

Operator request (via neurovista, 2026-06-28), in his words:
「composerでフィードバックを返して 空白率を返して thresholdを設けてエラーで
プロットできないように」 — return composer feedback, return the whitespace
ratio, set a threshold so it errors and cannot plot.

A sparse composite wastes the one resource a figure cannot get more of: page.
It also usually means the panels were sized for a different layout than the one
they ended up in, which is invisible in a thumbnail and obvious at print size.

WHITESPACE IS DERIVED, NOT RE-MEASURED. ``layout_report(fig)`` already computes
``coverage_frac`` (summed panel area) and ``empty_regions`` (maximal blank
rectangles), so whitespace is ``1 - coverage_frac`` and the regions name WHERE
the space went. Recomputing geometry here would give figrecipe two answers to
one question.

ENFORCEMENT IS OFF BY DEFAULT, and that is a deliberate departure from the
request as written. A raising default would break every existing sparse
composite at once — including work in flight — which is a disruptive default
change rather than a bug fix. So:

    max_whitespace_frac=None   (default)  measure and return; warn if very high
    max_whitespace_frac=0.4    enforce; raise above 40% blank

Turning enforcement on by default is the same decision, with the same blast
radius, as the overlap-severity question on
figrecipe-shape-overlap-detection-20260701. Both should be answered together
rather than promoting figure violations to errors in two uncoordinated steps.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Optional

#: Whitespace fraction above which the composite is reported as suspicious even
#: when enforcement is off. Not a failure threshold — a "look at this" line.
NOTEWORTHY_WHITESPACE_FRAC = 0.5


def compose_whitespace(fig: Any) -> Optional[Dict[str, Any]]:
    """Whitespace measurement for ``fig``, or None if it cannot be computed.

    Returns ``{"whitespace_frac", "coverage_frac", "empty_regions"}``. None
    means the layout could not be introspected — reported as unknown rather
    than defaulted to zero, which would read as "perfectly packed".
    """
    try:
        from .._composition._layout_report import layout_report

        report = layout_report(fig)
    except Exception:  # pragma: no cover - never break compose over a metric
        return None
    coverage = report.get("coverage_frac")
    if coverage is None:
        return None
    return {
        "whitespace_frac": max(0.0, 1.0 - float(coverage)),
        "coverage_frac": float(coverage),
        "empty_regions": report.get("empty_regions", []),
    }


def _describe_regions(regions, limit: int = 3) -> str:
    """The largest blank rectangles, in mm, so the message says WHERE."""
    sized = [r for r in regions if isinstance(r, dict)]
    sized.sort(key=lambda r: r.get("area_frac", 0.0), reverse=True)
    parts = []
    for r in sized[:limit]:
        box = r.get("bbox_mm")
        frac = r.get("area_frac")
        if box and frac is not None:
            parts.append(f"{frac:.0%} at {tuple(round(float(v), 1) for v in box)}mm")
        elif frac is not None:
            parts.append(f"{frac:.0%}")
    if not parts:
        return ""
    more = f" (+{len(sized) - limit} more)" if len(sized) > limit else ""
    return "; largest blank regions: " + ", ".join(parts) + more


def check_compose_whitespace(
    fig: Any,
    max_whitespace_frac: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Measure whitespace; raise when it exceeds ``max_whitespace_frac``.

    ``max_whitespace_frac=None`` measures without enforcing (the default —
    see the module docstring for why). Returns the measurement either way, or
    None when it could not be taken.
    """
    measured = compose_whitespace(fig)
    if measured is None:
        return None

    frac = measured["whitespace_frac"]
    where = _describe_regions(measured["empty_regions"])

    if max_whitespace_frac is not None and frac > max_whitespace_frac:
        raise ValueError(
            f"figrecipe [FR-COMPOSE-WHITESPACE]: composite is {frac:.0%} blank, "
            f"above the {max_whitespace_frac:.0%} limit this call set{where}. "
            f"Panels sized for one layout and placed in another is the usual "
            f"cause. Reduce the canvas, add columns, or grow the panels so the "
            f"page is used. To allow it deliberately, raise or clear "
            f"max_whitespace_frac on this compose call."
        )

    if frac > NOTEWORTHY_WHITESPACE_FRAC:
        warnings.warn(
            f"figrecipe: composite is {frac:.0%} blank{where}. Not an error — "
            f"no whitespace limit was set on this call — but over half the page "
            f"is empty, which usually means the panels were sized for a "
            f"different layout. Pass max_whitespace_frac=... to make this a "
            f"hard failure.",
            UserWarning,
            stacklevel=3,
        )
    return measured


__all__ = [
    "NOTEWORTHY_WHITESPACE_FRAC",
    "check_compose_whitespace",
    "compose_whitespace",
]

# EOF
