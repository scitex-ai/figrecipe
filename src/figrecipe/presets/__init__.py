#!/usr/bin/env python3
# Timestamp: 2026-03-13
# File: figrecipe/presets/__init__.py

"""Journal presets for publication-quality figures.

Provides standardized figure dimensions, DPI, fonts, and line widths
for major scientific journals. Works identically in both standalone
and cloud environments.

Usage:
    >>> from figrecipe.presets import get_journals, get_journal
    >>> presets = get_journals()
    >>> nature_single = get_journal("Standard", "single")
"""

from ._journals import get_journal, get_journals, mm_to_pixels
from ._scitex_style import (
    DPI_DISPLAY,
    DPI_PREVIEW,
    DPI_SAVE,
    SCITEX_STYLE,
    STYLE,
    get_default_dpi,
    get_display_dpi,
    get_preview_dpi,
    get_style,
    load_style,
    resolve_style_value,
    save_style,
    set_style,
)

__all__ = [
    "get_journals",
    "get_journal",
    "mm_to_pixels",
    # Flat SCITEX_STYLE preset (single source of truth: SCITEX_STYLE.yaml)
    "SCITEX_STYLE",
    "STYLE",
    "load_style",
    "save_style",
    "set_style",
    "get_style",
    "resolve_style_value",
    "get_default_dpi",
    "get_display_dpi",
    "get_preview_dpi",
    "DPI_SAVE",
    "DPI_DISPLAY",
    "DPI_PREVIEW",
]

# EOF
