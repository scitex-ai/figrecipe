#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect artists a recipe would draw that the figure no longer shows.

Card figrecipe-recipe-keeps-artists-removed-before-save-20260906, and the
coordinator's decision (2026-09-17) to take the DETECT-AND-WARN slice:
``ax.plot(...)`` then ``line.remove()`` before saving leaves the call in the
record, so a replay draws an artist the saved PNG does not show. **The defect
itself is not touched here** — no artist is removed, re-created or hidden, and
nothing about replay changes. The slice makes the state visible.

Why it is a check and not a fix: earlier passes established that a ``CallRecord``
carries NO handle to the artist it created (``_recorder/_core.py``: id /
function / args / kwargs / timestamp / ax_position / stats), so "is this artist
still alive?" cannot be asked of the record; and the escape hatches suggested
from that (``track=False`` among them) were tested and do not cover the general
family. Repair therefore needs the multi-part design change the card records; a
detector needs only facts both sides already have.

The check is CONSERVATIVE by construction — it can miss a removal, it must not
invent one:

* every method in :data:`ARTIST_METHODS` adds AT LEAST one artist to the axes,
  so ``live_artists < len(artist-producing records)`` means something that was
  drawn is no longer there; and
* the comparison is one-sided: more live artists than records (ticks, titles,
  legends, a user's own additions) is the normal case and says nothing, so it is
  not reported.

BOTH halves of the record must be passed in. An ``AxesRecord`` keeps ``calls``
(the data plotters) and ``decorations`` separate, and ``text`` / ``annotate`` /
the reference lines are DECORATIONS that create their own artist: handing this
module ``calls`` alone leaves the card's own headline case -- ``ax.text()`` then
``t.remove()`` -- undetectable, whatever the vocabulary says.

A false positive would be a bogus warning on every save, which would train users
to ignore it; a false negative leaves the user where they are today.

No matplotlib import — so it runs under the repo's expression tests — and the
caller passes plain counts.
"""

import warnings
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from .._params import PLOTTING_METHODS as _RECORDED_PLOTTING_METHODS

#: Methods that always leave at least one data artist on the axes. DERIVED from
#: the recorder's own vocabulary, never hand-copied: the first shipped slice of
#: this check listed 24 of the recorder's 49 plotters, so the artist of the other
#: 26 (``vlines``, ``hlines``, ``fill``, ``quiver``, ``psd``, ...) could be
#: removed and the figure still passed. The recorder's list is the definition of
#: "this call creates a data artist", so it is the only list that cannot drift
#: away from what the record actually holds.
PLOTTING_METHODS = frozenset(_RECORDED_PLOTTING_METHODS)

#: DECORATIONS that also leave an artist the live count covers. These are
#: recorded in the OTHER half of an ``AxesRecord`` (``decorations``, not
#: ``calls``), which is why the caller must pass both halves -- with calls alone
#: this whole vocabulary is unreachable, and the card's own headline case
#: (``ax.text()`` ... ``t.remove()``) is a removed decoration.
ARTIST_DECORATIONS = frozenset(
    {
        "text",  # -> ax.texts
        "annotate",  # -> ax.texts (plus one arrow patch)
        "arrow",  # -> ax.patches
        "axline",  # -> ax.lines
        "axhline",  # -> ax.lines
        "axvline",  # -> ax.lines
        "axhspan",  # -> ax.patches
        "axvspan",  # -> ax.patches
        "broken_barh",  # -> ax.patches
    }
)

#: Every recorded method whose artist the live count can see. A wrapper class
#: counts a method once: ``_recorder`` files each name into exactly one of the
#: two halves.
ARTIST_METHODS = PLOTTING_METHODS | ARTIST_DECORATIONS

#: Decorations deliberately NOT counted, each for a measured reason rather than
#: for tidiness -- counting any of them would warn on a figure that lost nothing:
#: ``table`` lands in ``ax.tables``, ``legend`` in ``ax.legend_``, and
#: ``set_title`` / ``set_xlabel`` / the tick setters configure an axis object;
#: none of those containers is in the live count. ``clabel`` draws a label only
#: for a contour level that is actually labelled, so it is not a guaranteed one.
NON_ARTIST_DECORATIONS = frozenset(
    {
        "table",
        "legend",
        "grid",
        "axis",
        "set_title",
        "set_xlabel",
        "set_ylabel",
        "set_xlim",
        "set_ylim",
        "set_xscale",
        "set_yscale",
        "set_aspect",
        "set_xticks",
        "set_yticks",
        "set_xticklabels",
        "set_yticklabels",
        "tick_params",
        "margins",
        "rotate_labels",
        "stat_annotation",
        "clabel",
    }
)


class ArtistLifecycleWarning(UserWarning):
    """A recipe is not faithful to the figure it was saved from.

    A warning, never an error: the figure the user sees is correct and the
    mismatch appears only on replay, so refusing to save would destroy work in
    order to report a property of the recording.
    """


def minimum_artists_for(records: Iterable[object]) -> Optional[int]:
    """The fewest artists the given records can account for.

    Each record in :data:`ARTIST_METHODS` adds one or more; anything else adds
    none that can be asserted. Both halves of the axes record belong here — a
    data ``call`` and an artist-bearing ``decoration`` alike. ``None`` when
    there is nothing to compare against (no artist-producing record at all), so
    a figure carrying only a title or a legend is never flagged.
    """
    artist_records = sum(
        1
        for record in records
        if getattr(record, "function", None) in ARTIST_METHODS
    )
    return artist_records if artist_records > 0 else None


@dataclass(frozen=True)
class RemovalReport:
    """A figure showing fewer artists than its calls require at minimum."""

    axes_key: str
    #: Fewest artists the recorded plotting calls must have added.
    minimum: int
    #: Artists the axes currently holds.
    live: int

    @property
    def missing(self) -> int:
        """The shortfall, i.e. at least this many artists were removed."""
        return max(self.minimum - self.live, 0)


def detect_removals(
    axes_key: str,
    records: Sequence[object],
    live_artists: int,
) -> Optional[RemovalReport]:
    """The mismatch for one axes, or None when there is nothing to say.

    ``records`` is every artist-producing entry of that axes' record, from BOTH
    halves (``calls`` and ``decorations``).
    """
    minimum = minimum_artists_for(records)
    if minimum is None or live_artists >= minimum:
        return None
    return RemovalReport(axes_key=axes_key, minimum=minimum, live=live_artists)


def removals_in_figure(axes: Iterable[tuple]) -> List[RemovalReport]:
    """Every axes mismatch, given ``(key, records, live_artist_count)`` triples."""
    reports: List[RemovalReport] = []
    for key, records, live in axes:
        report = detect_removals(key, records, live)
        if report is not None:
            reports.append(report)
    return reports


def warn_removals(reports: Sequence[RemovalReport]) -> int:
    """Warn once about removed-but-recorded artists; return how many.

    The message states the fact, the consequence, the fact that the check is
    conservative, and the action a user actually has. It deliberately does NOT
    name a flag that was measured not to fix this, and does not pretend the
    recipe can be repaired for them.
    """
    if not reports:
        return 0
    shortfall = sum(report.missing for report in reports)
    where = ", ".join(f"{r.axes_key} (≥{r.missing})" for r in reports[:5])
    warnings.warn(
        f"figrecipe: this figure holds fewer artists than its recorded calls "
        f"and decorations require ({where}), so at least {shortfall} artist(s) "
        f"were removed after being drawn and a replay will draw what this "
        f"figure does not show. The figure is correct; the recipe is not "
        f"faithful to it. The check is conservative (it can miss a removal, not "
        f"invent one). To fix the recipe, draw conditional on the same decision "
        f"that led to the removal (e.g. `if keep: ax.plot(...)`) or drop the "
        f"call from the record. Nothing was changed for you.",
        ArtistLifecycleWarning,
        stacklevel=3,
    )
    return shortfall


__all__ = [
    "ARTIST_DECORATIONS",
    "ARTIST_METHODS",
    "NON_ARTIST_DECORATIONS",
    "PLOTTING_METHODS",
    "ArtistLifecycleWarning",
    "RemovalReport",
    "detect_removals",
    "minimum_artists_for",
    "removals_in_figure",
    "warn_removals",
]

# EOF
