#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Internal axis helper utilities for matplotlib axes.

This is an internal module. Use the public API instead:
    from figrecipe.styles import hide_spines, rotate_labels
    # Or via RecordingAxes methods:
    ax.hide_spines()
    ax.rotate_labels(x=45)
"""

# Thousands-separator formatting
from ._comma_format import CommaFormatter, comma_format

# Geometry utilities
from ._geometry import extend, force_aspect

# Label rotation
from ._rotate_labels import rotate_labels

# Scientific notation
from ._sci_note import OOMFormatter, sci_note

# Spine visibility
from ._spines import (
    hide_spines,
    show_all_spines,
    show_classic_spines,
    show_spines,
    toggle_spines,
)

# Tick utilities
from ._ticks import map_ticks, set_n_ticks, set_ticks, set_x_ticks, set_y_ticks

__all__ = [
    # Label rotation
    "rotate_labels",
    # Spine visibility
    "hide_spines",
    "show_spines",
    "show_all_spines",
    "show_classic_spines",
    "toggle_spines",
    # Tick utilities
    "set_n_ticks",
    "set_ticks",
    "set_x_ticks",
    "set_y_ticks",
    "map_ticks",
    # Scientific notation
    "sci_note",
    "OOMFormatter",
    # Thousands-separator formatting
    "comma_format",
    "CommaFormatter",
    # Geometry
    "force_aspect",
    "extend",
]
