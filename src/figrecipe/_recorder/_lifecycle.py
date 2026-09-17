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

* every method in :data:`PLOTTING_METHODS` adds AT LEAST one artist to the axes,
  so ``live_artists < len(plotting calls)`` means something that was drawn is no
  longer there; and
* the comparison is one-sided: more live artists than calls (decorations, ticks,
  a user's own additions) is the normal case and says nothing, so it is not
  reported.

A false positive would be a bogus warning on every save, which would train users
to ignore it; a false negative leaves the user where they are today.

Stdlib only — no matplotlib import — so it runs under the repo's expression
tests, and the caller passes plain counts.
"""

import warnings
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

#: Methods that always leave at least one artist on the axes. Anything that only
#: configures existing artwork (``set_*``, ``legend``, ``grid``, the annotations
#: of labels) is deliberately absent: counting those would overstate the minimum
#: and turn this into a source of false alarms.
PLOTTING_METHODS = frozenset(
    {
        "plot",
        "scatter",
        "bar",
        "barh",
        "hist",
        "hist2d",
        "imshow",
        "matshow",
        "fill_between",
        "fill_betweenx",
        "errorbar",
        "stem",
        "step",
        "stackplot",
        "boxplot",
        "violinplot",
        "pie",
        "contour",
        "contourf",
        "pcolormesh",
        "eventplot",
        "specgram",
        "hexbin",
        "arrow",
    }
)


class ArtistLifecycleWarning(UserWarning):
    """A recipe is not faithful to the figure it was saved from.

    A warning, never an error: the figure the user sees is correct and the
    mismatch appears only on replay, so refusing to save would destroy work in
    order to report a property of the recording.
    """


def minimum_artists_for(calls: Iterable[object]) -> Optional[int]:
    """The fewest artists the given calls can account for.

    Each call in :data:`PLOTTING_METHODS` adds one or more; anything else adds
    none that can be asserted. ``None`` when there is nothing to compare against
    (no plotting calls at all), so a figure with only decorations is never
    flagged.
    """
    plotting = sum(
        1
        for call in calls
        if getattr(call, "function", None) in PLOTTING_METHODS
    )
    return plotting if plotting > 0 else None


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
    calls: Sequence[object],
    live_artists: int,
) -> Optional[RemovalReport]:
    """The mismatch for one axes, or None when there is nothing to say."""
    minimum = minimum_artists_for(calls)
    if minimum is None or live_artists >= minimum:
        return None
    return RemovalReport(axes_key=axes_key, minimum=minimum, live=live_artists)


def removals_in_figure(axes: Iterable[tuple]) -> List[RemovalReport]:
    """Every axes mismatch, given ``(key, calls, live_artist_count)`` triples."""
    reports: List[RemovalReport] = []
    for key, calls, live in axes:
        report = detect_removals(key, calls, live)
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
        f"require ({where}), so at least {shortfall} artist(s) were removed "
        f"after being drawn and a replay will draw what this figure does not "
        f"show. The figure is correct; the recipe is not faithful to it. The "
        f"check is conservative (it can miss a removal, not invent one). To fix "
        f"the recipe, draw conditional on the same decision that led to the "
        f"removal (e.g. `if keep: ax.plot(...)`) or drop the call from the "
        f"record. Nothing was changed for you.",
        ArtistLifecycleWarning,
        stacklevel=3,
    )
    return shortfall


__all__ = [
    "ArtistLifecycleWarning",
    "PLOTTING_METHODS",
    "RemovalReport",
    "detect_removals",
    "minimum_artists_for",
    "removals_in_figure",
    "warn_removals",
]

# EOF
