#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ruff: noqa: F401 - Re-exports are intentional
"""Style management for figrecipe.

Provides style loading, application, and management for publication-quality figures.

Usage:
    from figrecipe.styles import load_style, STYLE

    # Load default style
    style = load_style()

    # Access style parameters
    print(style.axes.width_mm)
    print(style.fonts.axis_label_pt)

Public API:
    Style Management:
        - load_style, unload_style, list_presets, STYLE

    Axis Helpers (also available as ax.method() via RecordingAxes):
        - hide_spines, show_spines, toggle_spines
        - rotate_labels, set_n_ticks, map_ticks
        - sci_note, comma_format, force_aspect, extend

    Font Utilities:
        - check_font, list_available_fonts
"""

# =============================================================================
# PUBLIC API - User-facing functions only
# =============================================================================

# Style management
# Axis helper utilities (user-facing)
from ._axis_helpers import CommaFormatter as CommaFormatter
from ._axis_helpers import comma_format as comma_format
from ._axis_helpers import extend as extend
from ._axis_helpers import force_aspect as force_aspect
from ._axis_helpers import hide_spines as hide_spines
from ._axis_helpers import map_ticks as map_ticks
from ._axis_helpers import rotate_labels as rotate_labels
from ._axis_helpers import sci_note as sci_note
from ._axis_helpers import set_n_ticks as set_n_ticks
from ._axis_helpers import set_ticks as set_ticks
from ._axis_helpers import set_x_ticks as set_x_ticks
from ._axis_helpers import set_y_ticks as set_y_ticks
from ._axis_helpers import show_all_spines as show_all_spines
from ._axis_helpers import show_classic_spines as show_classic_spines
from ._axis_helpers import show_spines as show_spines
from ._axis_helpers import toggle_spines as toggle_spines
from ._fonts import check_font as check_font
from ._fonts import list_available_fonts as list_available_fonts
from ._fonts import register_arial_fonts as register_arial_fonts
from ._style_loader import STYLE as STYLE
from ._style_loader import list_presets as list_presets
from ._style_loader import load_style as load_style
from ._style_loader import unload_style as unload_style

# =============================================================================
# __all__ - Controls tab-completion and import *, keep minimal and user-focused
# =============================================================================
__all__ = [
    # Style management
    "load_style",
    "unload_style",
    "list_presets",
    "STYLE",
    # Font utilities
    "check_font",
    "list_available_fonts",
    "register_arial_fonts",
    # Axis helper utilities (user-facing)
    "hide_spines",
    "show_spines",
    "show_all_spines",
    "show_classic_spines",
    "toggle_spines",
    "rotate_labels",
    "set_n_ticks",
    "set_ticks",
    "set_x_ticks",
    "set_y_ticks",
    "map_ticks",
    "sci_note",
    "comma_format",
    "CommaFormatter",
    "force_aspect",
    "extend",
]

# EOF
