#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions for power users.

This module exposes utility functions that are not part of the core API
but may be useful for advanced use cases.

Usage
-----
>>> from figrecipe import utils
>>> mm = utils.inch_to_mm(1.0)  # 25.4

>>> # Or import specific functions
>>> from figrecipe.utils import mm_to_inch, check_font
"""

from ._api._notebook import enable_svg
from ._api._panel import panel_label
from ._api._seaborn_proxy import sns
from ._api._style_manager import STYLE, apply_style
from ._composition import (
    AlignmentMode,
    align_panels,
    align_smart,
    distribute_panels,
    hide_panel,
    import_axes,
    show_panel,
    toggle_panel,
)
from ._integrations import (
    SCITEX_STATS_AVAILABLE,
    annotate_from_stats,
    from_scitex_stats,
)
from ._recorder import CallRecord, FigureRecord
from ._reproducer import get_recipe_info
from ._serializer import load_recipe
from ._utils._numpy_io import CsvFormat, DataFormat, load_array, save_array
from ._utils._units import (
    MM_PER_INCH,  # noqa: F401  (re-exported via __all__)
    inch_to_mm,
    mm_to_inch,
    mm_to_pt,
    mm_to_scatter_size,
    normalize_color,
    pt_to_mm,
)
from ._quality._validator import ValidationResult
from ._wrappers import RecordingAxes, RecordingFigure
from .styles._style_applier import check_font, list_available_fonts

__all__ = [
    # Unit conversions
    "MM_PER_INCH",
    "mm_to_inch",
    "inch_to_mm",
    "mm_to_pt",
    "pt_to_mm",
    "mm_to_scatter_size",
    "normalize_color",
    # Font utilities
    "check_font",
    "list_available_fonts",
    # Data I/O
    "CsvFormat",
    "DataFormat",
    "load_array",
    "save_array",
    # Record types
    "CallRecord",
    "FigureRecord",
    "ValidationResult",
    "RecordingAxes",
    "RecordingFigure",
    "load_recipe",
    "get_recipe_info",
    # Composition (advanced)
    "AlignmentMode",
    "align_panels",
    "align_smart",
    "distribute_panels",
    "hide_panel",
    "import_axes",
    "show_panel",
    "toggle_panel",
    # Panel label
    "panel_label",
    # Style (advanced)
    "STYLE",
    "apply_style",
    # Notebook/seaborn
    "enable_svg",
    "sns",
    # scitex.stats integration
    "SCITEX_STATS_AVAILABLE",
    "annotate_from_stats",
    "from_scitex_stats",
]
