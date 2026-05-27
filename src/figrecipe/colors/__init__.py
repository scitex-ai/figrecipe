#!/usr/bin/env python3
"""figrecipe color utilities — RGB, RGBA, HEX conversions and palettes."""

# Public API — universal converters and colormap utilities
from ._add_hue_col import add_hue_col
from ._colormap import (
    get_categorical_colors_from_cmap,
    get_color_from_cmap,
    get_colors_from_cmap,
)
from ._colors import (
    cycle_color,
    gradiate_color,
    to_hex,
    to_rgb,
    to_rgba,
    update_alpha,
)
from ._interpolate import gen_interpolate, interpolate
from ._PARAMS import (  # noqa: F401
    DEF_ALPHA,
    HEX,
    PARAMS,
    RGB,
    RGB_NORM,
    RGBA,
    RGBA_NORM,
)
from ._vizualize_colors import vizualize_colors

# Internal functions remain accessible via figrecipe.colors._colors.bgr2rgb etc.
# but are not re-exported here to keep the public API clean.

__all__ = [
    # Color dictionaries
    "RGB",
    "RGBA",
    "HEX",
    # Universal converters
    "to_hex",
    "to_rgb",
    "to_rgba",
    "update_alpha",
    # Color cycling
    "cycle_color",
    # Gradients & interpolation
    "gradiate_color",
    "interpolate",
    "gen_interpolate",
    # Colormap utilities
    "get_color_from_cmap",
    "get_colors_from_cmap",
    "get_categorical_colors_from_cmap",
    # DataFrame / visualization helpers
    "add_hue_col",
    "vizualize_colors",
]

# EOF
