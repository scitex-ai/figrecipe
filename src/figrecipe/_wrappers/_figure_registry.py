#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Weak registry mapping raw matplotlib Figures to their RecordingFigure wrapper.

The module-level ``figrecipe.pyplot.colorbar`` wrapper only ever sees the RAW
current figure -- via ``plt.gcf()``, a mappable's axes, or an explicit ``cax``
axes. To record a MANUAL ``plt.colorbar(...)`` call it must find the owning
``RecordingFigure`` so the call routes through ``RecordingFigure.colorbar`` and
lands in the recipe (surviving a recipe round-trip). This registry provides that
raw-figure -> wrapper lookup. ``RecordingFigure.__init__`` registers itself here.

Keyed by ``id(raw_fig)`` (matplotlib ``Figure`` instances are not usable as
``WeakValueDictionary`` keys), with the wrapper held weakly so a closed/dropped
figure does not leak.
"""

from typing import TYPE_CHECKING, Optional
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from ._figure import RecordingFigure

# id(raw matplotlib Figure) -> RecordingFigure wrapper (held weakly).
_RAW_FIG_TO_WRAPPER: "WeakValueDictionary[int, RecordingFigure]" = WeakValueDictionary()


def register_recording_figure(raw_fig, wrapper: "RecordingFigure") -> None:
    """Register ``wrapper`` as the RecordingFigure for raw ``raw_fig``."""
    if raw_fig is None:
        return
    try:
        _RAW_FIG_TO_WRAPPER[id(raw_fig)] = wrapper
    except TypeError:
        # Some mock/headless figures are not weak-referenceable; recording
        # via the module-level wrapper is then simply unavailable for them.
        pass


def get_recording_figure(raw_fig) -> Optional["RecordingFigure"]:
    """Return the ``RecordingFigure`` wrapping ``raw_fig`` (or None)."""
    if raw_fig is None:
        return None
    return _RAW_FIG_TO_WRAPPER.get(id(raw_fig))


__all__ = ["register_recording_figure", "get_recording_figure"]

# EOF
