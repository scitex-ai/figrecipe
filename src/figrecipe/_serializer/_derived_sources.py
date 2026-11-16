#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which files a saved figure was derived from -- known, never guessed.

A figure rebuilt by ``fr.reproduce(recipe)`` is determined by exactly the
files figrecipe read to rebuild it: the recipe YAML, its data files, and an
applied ``.overrides.json``. ``reproduce`` snapshots that list together with
a fingerprint of the figure's record. At save time the declaration is used
ONLY if the record is unchanged since the snapshot: any later plotting call,
decoration, label or style change may carry in-memory data figrecipe cannot
trace, so the figure is then recorded undeclared (clew keeps every input of
the run). Figures built from in-memory arrays are never declared.

Recipes reproduced from a ZIP/directory bundle are not declared either: they
are rebuilt from an extracted temporary copy that no longer exists.
"""

from __future__ import annotations

import contextvars
import functools
import hashlib
import json
from typing import Any, Callable, List, Optional

from ._clew import declaring, is_tracking

# ``figure`` fields a SAVE writes back into the record (live size/dpi/layout
# sync, crop geometry, captured layout, rcParams, the clew stamp). They carry
# geometry, never data, and are excluded from the fingerprint so saving the
# same unchanged figure twice still declares its sources.
_SAVE_TIME_FIGURE_FIELDS = frozenset(
    {
        "figsize",
        "dpi",
        "layout",
        "constrained_layout",
        "crop_info",
        "content_bbox",
        "content_size_mm",
        "mm_layout",
        "layout_collapsed",
        "rcparams",
        "clew_tracked",
    }
)
_SAVE_TIME_AXES_FIELDS = frozenset(
    {"bbox", "bbox_uncropped", "final_xlim", "final_ylim", "final_spines"}
)
_SAVE_TIME_COLORBAR_FIELDS = frozenset({"cax_bbox"})


def _default(value: Any) -> Any:
    tobytes = getattr(value, "tobytes", None)
    if callable(tobytes):
        digest = hashlib.sha256(tobytes()).hexdigest()
        return f"<array {getattr(value, 'shape', '')} {value.dtype} {digest}>"
    return repr(value)


def _content(record) -> dict:
    data = record.to_dict()
    figure = data.get("figure") or {}
    for key in _SAVE_TIME_FIGURE_FIELDS:
        figure.pop(key, None)
    for ax in (data.get("axes") or {}).values():
        if isinstance(ax, dict):
            for key in _SAVE_TIME_AXES_FIELDS:
                ax.pop(key, None)
    colorbars = figure.get("colorbars")
    if isinstance(colorbars, list):
        figure["colorbars"] = [
            {k: v for k, v in cb.items() if k not in _SAVE_TIME_COLORBAR_FIELDS}
            if isinstance(cb, dict)
            else cb
            for cb in colorbars
        ]
    return data


def record_fingerprint(record) -> str:
    """Stable hash of everything in ``record`` that determines the figure."""
    blob = json.dumps(_content(record), sort_keys=True, default=_default)
    return hashlib.sha256(blob.encode()).hexdigest()


def snapshot_sources(record, sources: List[str]) -> None:
    """Remember that ``record`` was rebuilt from exactly ``sources``."""
    record._clew_sources = list(sources)
    record._clew_fingerprint = record_fingerprint(record)


def declared_sources(fig) -> Optional[List[str]]:
    """The files ``fig`` is derived from, or None when that is not known."""
    record = getattr(fig, "record", None)
    sources = getattr(record, "_clew_sources", None)
    if sources is None:
        return None
    if record_fingerprint(record) != getattr(record, "_clew_fingerprint", None):
        return None
    return list(sources)


def declares_figure_sources(save_fn: Callable) -> Callable:
    """Decorate a ``save(fig, ...)`` so its clew outputs carry the declaration.

    The sources are decided ONCE, before the save mutates the record, and
    apply to every output the save records (image, recipe, data CSVs).
    Without an active clew session nothing is computed.
    """

    @functools.wraps(save_fn)
    def wrapper(fig, *args, **kwargs):
        if _IN_SAVE.get() is fig:  # save_figure -> fig.save_recipe: keep outer
            return save_fn(fig, *args, **kwargs)
        sources = declared_sources(fig) if is_tracking() else None
        token = _IN_SAVE.set(fig)
        try:
            with declaring(sources):
                return save_fn(fig, *args, **kwargs)
        finally:
            _IN_SAVE.reset(token)

    return wrapper


# The figure whose save is in progress (its nested save_recipe reuses the
# declaration decided before the save started mutating the record).
_IN_SAVE: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "figrecipe_in_declared_save", default=None
)


__all__ = [
    "declared_sources",
    "declares_figure_sources",
    "record_fingerprint",
    "snapshot_sources",
]

# EOF
