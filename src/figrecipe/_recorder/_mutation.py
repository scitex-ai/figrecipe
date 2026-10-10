#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write each mutated artist's FINAL state back into its recorded call.

Card figrecipe-handle-mutation-after-draw-not-recorded-20260927's remainder
(root cause 2, DATA/styling half): a call is recorded, then the artist handle
is mutated before save (``line.set_data()``, ``line.set_color()``). Only the
kwargs present at call time reach the recipe, so the replay reconstructs the
artist as first drawn -- a different dataset in the set_data case.

The repair re-reads the live artist at save time and writes the final state
into the record -- the same shape as the PR #426 visibility annotation
(:mod:`figrecipe._recorder._visibility`), which writes final visibility, and
the removal reconcile, which drops calls whose artists left. Nothing is
dropped here: the artist is still on the figure, so its record is updated.

Conservatism (same reason as both precedents -- a wrong edit rewrites the
user's own recipe):

* only ``plot`` calls whose record maps to EXACTLY ONE live artist are
  touched; multi-line plots, unregistered calls and released/detached artists
  are left alone (fail-open, no guess);
* the artist must duck-type as a Line2D (``get_xdata``/``get_ydata``/
  ``get_color``); anything else is left alone;
* the record's x/y arg entries must be found by name; anything else
  (fmt-string plots, datetime axes that do not survive a float cast) is left
  alone;
* a field is rewritten only when the final value DIFFERS, so an untouched
  figure's record is byte-identical.

No matplotlib import at module level: the decision functions duck-type the
artist and read plain attributes, so they run under the repo's expression
tests (same rule as :mod:`figrecipe._recorder._visibility`).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set

import numpy as np

from ._artists import noted_artists

#: Record functions the re-read covers. ``plot`` is the measured case;
#: anything else is left alone (fail-open).
MUTATABLE_FUNCTIONS = ("plot",)


@dataclass
class MutatedCall:
    """A record whose kwargs/args gained the artist's final state."""

    axes_key: str
    call_id: str
    function: str
    half: str
    fields: List[str] = field(default_factory=list)


def _live_artist(refs: Optional[Sequence[Any]], live_ids: Set[int]) -> Any:
    """The single live artist behind ``refs``, else None (fail-open).

    The strong reference is held while the identity is checked, so a
    recycled ``id()`` can never stand in for the artist itself (same rule as
    the visibility/removal repairs).
    """
    if not refs or len(refs) != 1:
        return None
    artist = refs[0]()
    if artist is None or id(artist) not in live_ids:
        return None
    return artist


def _is_line(artist: Any) -> bool:
    get_x = getattr(artist, "get_xdata", None)
    get_y = getattr(artist, "get_ydata", None)
    get_c = getattr(artist, "get_color", None)
    return callable(get_x) and callable(get_y) and callable(get_c)


def _float_array(values: Any) -> Optional[np.ndarray]:
    try:
        return np.asarray(values, dtype=float)
    except (TypeError, ValueError):
        return None


def _recorded_array(entry: Any) -> Optional[np.ndarray]:
    """The numeric data a processed record arg entry carries, else None."""
    if not isinstance(entry, dict):
        return None
    blob = entry.get("_array", None)
    if blob is not None:
        return _float_array(blob)
    data = entry.get("data", None)
    if isinstance(data, list):
        return _float_array(data)
    return None


def _same(first: np.ndarray, second: np.ndarray) -> bool:
    return first.shape == second.shape and bool(np.all(first == second))


def _write_data(entry: Dict[str, Any], live: np.ndarray) -> None:
    arr = np.asarray(live)
    entry["_array"] = arr
    entry["dtype"] = str(arr.dtype)
    if entry.get("data") != "__FILE__":
        entry["data"] = arr.tolist()


def _rgba_list(color: Any) -> Optional[List[float]]:
    import matplotlib.colors as mcolors

    try:
        r, g, b, _a = mcolors.to_rgba(color)
    except (ValueError, TypeError):
        return None
    return [float(r), float(g), float(b)]


def _reread_plot_record(record: Any, registry: Dict[int, tuple], live_ids: Set[int]) -> List[str]:
    """Refresh one ``plot`` record from its live Line2D. Returns changed fields."""
    artist = _live_artist(noted_artists(registry, record), live_ids)
    if artist is None or not _is_line(artist):
        return []
    args = getattr(record, "args", None)
    kwargs = getattr(record, "kwargs", None)
    if not isinstance(args, list) or not isinstance(kwargs, dict):
        return []
    by_name = {a.get("name"): a for a in args if isinstance(a, dict)}
    if "x" not in by_name or "y" not in by_name:
        return []
    live_x = _float_array(artist.get_xdata())
    live_y = _float_array(artist.get_ydata())
    if live_x is None or live_y is None:
        return []
    changed: List[str] = []
    pending = []
    for name, live in (("x", live_x), ("y", live_y)):
        recorded = _recorded_array(by_name[name])
        if recorded is None:
            return []
        if not _same(recorded, live):
            pending.append((name, live))
    for name, live in pending:
        _write_data(by_name[name], live)
        changed.append(f"data:{name}")
    if "color" in kwargs:
        live_color = _rgba_list(artist.get_color())
        recorded_color = _float_array(kwargs.get("color"))
        if (
            live_color is not None
            and recorded_color is not None
            and recorded_color.shape == (3,)
            and not _same(recorded_color, np.asarray(live_color))
        ):
            kwargs["color"] = live_color
            changed.append("style:color")
    return changed


def annotate_mutated(
    records: Sequence[Any],
    registry: Dict[int, tuple],
    live_ids: Set[int],
    axes_key: str,
    half: str,
) -> List[MutatedCall]:
    """Write each mutated Line2D's final data/style into its ``plot`` record.

    Mutates ``record.args``/``record.kwargs`` in place -- the record object is
    what the save pipeline serializes -- and returns what changed. Returns
    ``[]`` for an ordinary figure: a field is rewritten only when the final
    value differs, so untouched records are byte-identical.
    """
    mutated: List[MutatedCall] = []
    for record in records:
        if str(getattr(record, "function", "")) not in MUTATABLE_FUNCTIONS:
            continue
        fields = _reread_plot_record(record, registry, live_ids)
        if not fields:
            continue
        mutated.append(
            MutatedCall(
                axes_key=axes_key,
                call_id=str(getattr(record, "id", "?")),
                function=str(getattr(record, "function", "")),
                half=half,
                fields=fields,
            )
        )
    return mutated
