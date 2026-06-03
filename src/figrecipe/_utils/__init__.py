#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility modules for figrecipe."""

from ._bundle import is_bundle_path, resolve_recipe_path
from ._calc_nice_ticks import calc_nice_ticks
from ._close import close  # noqa: F401
from ._colorbar import add_colorbar, style_colorbar  # noqa: F401
from ._csv_column_naming import (  # noqa: F401
    get_csv_column_name,
    get_csv_column_prefix,
    get_trace_columns_from_df,
    get_unique_trace_id,
    parse_csv_column_name,
    sanitize_id,
)
from ._diff import get_non_default_kwargs, is_default_value
from ._dimension_info import get_dimension_info, print_dimension_info  # noqa: F401
from ._dimension_viewer import compare_modes  # noqa: F401
from ._get_actual_font import get_actual_font_name  # noqa: F401
from ._grid import grid_id, parse_grid_id  # noqa: F401
from ._histogram_utils import HistogramBinManager  # noqa: F401
from ._im2grid import im2grid  # noqa: F401
from ._is_valid_axis import assert_valid_axis, is_valid_axis  # noqa: F401
from ._mk_colorbar import mk_colorbar  # noqa: F401
from ._mk_patches import mk_patches  # noqa: F401
from ._nice_lim import nice_lim
from ._numpy_io import load_array, save_array
from ._units import inch_to_mm, mm_to_inch, mm_to_pt, pt_to_mm

__all__ = [
    "HistogramBinManager",
    "add_colorbar",
    "assert_valid_axis",
    "calc_nice_ticks",
    "close",
    "compare_modes",
    "get_actual_font_name",
    "get_csv_column_name",
    "get_csv_column_prefix",
    "get_dimension_info",
    "get_non_default_kwargs",
    "get_trace_columns_from_df",
    "get_unique_trace_id",
    "grid_id",
    "im2grid",
    "inch_to_mm",
    "is_bundle_path",
    "is_default_value",
    "is_valid_axis",
    "load_array",
    "mk_colorbar",
    "mk_patches",
    "mm_to_inch",
    "mm_to_pt",
    "nice_lim",
    "parse_csv_column_name",
    "parse_grid_id",
    "print_dimension_info",
    "pt_to_mm",
    "resolve_recipe_path",
    "sanitize_id",
    "save_array",
    "style_colorbar",
]

# Optional extras (imports must stay below to satisfy ImportError fallbacks).
try:
    from ._image_diff import (  # noqa: F401, E402
        compare_images,
        create_comparison_figure,
    )

    __all__.extend(["compare_images", "create_comparison_figure"])
except ImportError:
    pass

try:
    from ._crop import crop, find_content_area  # noqa: F401, E402

    __all__.extend(["crop", "find_content_area"])
except ImportError:
    pass

try:
    from ._hitmap import create_hitmap, generate_hitmap_report  # noqa: F401, E402

    __all__.extend(["create_hitmap", "generate_hitmap_report"])
except ImportError:
    pass
