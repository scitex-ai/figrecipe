#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture + restore the full active matplotlib rcParams for faithful replay.

The recipe's curated ``style`` block holds figrecipe's own parameters, but a
figure can also depend on rcParams set by a loaded theme (e.g. SCITEX_STYLE) or
set globally by the user -- ``axes.titleweight``, ``font.weight``, ``font.style``,
tick direction, minor-tick visibility, and so on. Those are NOT in the curated
block, so without capturing them a fresh-process replay renders with matplotlib
defaults and diverges from the original (a silent reproduction failure).

This module snapshots the rcParams that differ from ``matplotlib.rcParamsDefault``
as YAML-safe primitives at figure-build time (the theme is persisted as concrete
values, not a style name), and restores them inside an ``rc_context`` on replay
so the figure renders in the identical environment -- pixel-identical, in all
cases.
"""

import warnings
from typing import Any, Dict

import matplotlib as mpl

# rcParams that route OUTPUT or describe the ENVIRONMENT rather than the figure's
# appearance: replaying them would hijack the reproduce environment, and figure
# size / dpi are already captured as record.figsize / record.dpi. Excluded by
# exact key or by "prefix." membership.
_EXCLUDE_EXACT = frozenset(
    {
        "backend",
        "interactive",
        "toolbar",
        "timezone",
        "datapath",
        "figure.figsize",
        "figure.dpi",
        "savefig.dpi",
        "savefig.directory",
        "savefig.format",
        "docstring.hardcopy",
        "examples.directory",
    }
)
_EXCLUDE_PREFIXES = (
    "backend_",
    "webagg.",
    "tk.",
    "macosx.",
    "keymap.",
    "animation.",
)


def _excluded(key: str) -> bool:
    if key in _EXCLUDE_EXACT:
        return True
    return any(key.startswith(p) for p in _EXCLUDE_PREFIXES)


def _to_primitive(value: Any) -> Any:
    """Convert an rcParam value to a YAML-safe, round-trippable primitive."""
    from cycler import Cycler

    if isinstance(value, Cycler):
        return {
            "__cycler__": {
                k: [_to_primitive(x) for x in v] for k, v in value.by_key().items()
            }
        }
    if isinstance(value, (list, tuple)):
        return [_to_primitive(v) for v in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float, str)):
        return value
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    return str(value)


def capture_rcparams_delta() -> Dict[str, Any]:
    """Snapshot rcParams that differ from the library default, as primitives."""
    default = mpl.rcParamsDefault
    delta: Dict[str, Any] = {}
    for key in mpl.rcParams:
        if _excluded(key):
            continue
        cur = mpl.rcParams[key]
        dft = default.get(key)
        try:
            same = bool(cur == dft)
        except (ValueError, TypeError):
            same = repr(cur) == repr(dft)
        if not same:
            delta[key] = _to_primitive(cur)
    return delta


def _from_primitive(value: Any) -> Any:
    from cycler import cycler

    if isinstance(value, dict) and "__cycler__" in value:
        by_key = value["__cycler__"]
        out = None
        for k, vals in by_key.items():
            c = cycler(k, list(vals))
            out = c if out is None else out + c
        return out
    return value


def apply_recorded_rcparams(rcparams: Dict[str, Any]) -> None:
    """Apply recorded rcParams onto the live (rc_context-scoped) rcParams.

    Keys are set individually; one matplotlib rejects is WARNED (fail loud), not
    silently dropped -- a genuinely unreproducible parameter is made visible
    rather than masked. Call inside ``matplotlib.rc_context()`` so it never leaks
    to the global state.
    """
    if not rcparams:
        return
    for key, value in rcparams.items():
        try:
            mpl.rcParams[key] = _from_primitive(value)
        except (KeyError, ValueError) as exc:
            warnings.warn(
                f"figrecipe: could not restore rcParam {key!r}={value!r} on "
                f"replay ({exc}); reproduction may diverge for this parameter.",
                stacklevel=2,
            )
