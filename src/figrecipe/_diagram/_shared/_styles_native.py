#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Native matplotlib diagram styling using figrecipe SCITEX colors.

Derives all colors from the SCITEX preset palette defined in
``styles/presets/SCITEX.yaml`` rather than hardcoding hex values.
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# SCITEX palette (source of truth: styles/presets/SCITEX.yaml colors.rgb)
# Kept as constants so diagram/diagram code works without load_style().
# ---------------------------------------------------------------------------
_SCITEX_RGB = {
    "blue": (0, 128, 192),
    "red": (255, 70, 50),
    "green": (20, 180, 20),
    "yellow": (230, 160, 20),
    "purple": (200, 50, 255),
    "lightblue": (20, 200, 200),
    "orange": (228, 94, 50),
    "pink": (255, 150, 200),
    "gray": (128, 128, 128),
    "brown": (128, 0, 0),
    "navy": (0, 0, 100),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
}


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert (r, g, b) 0-255 to hex string."""
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def _lighten(rgb: Tuple[int, int, int], factor: float = 0.75) -> str:
    """Blend color toward white. factor=1.0 → white, 0.0 → original."""
    r = int(rgb[0] + (255 - rgb[0]) * factor)
    g = int(rgb[1] + (255 - rgb[1]) * factor)
    b = int(rgb[2] + (255 - rgb[2]) * factor)
    return _rgb_to_hex((r, g, b))


def _darken(rgb: Tuple[int, int, int], factor: float = 0.4) -> str:
    """Blend color toward black. factor=1.0 → black, 0.0 → original."""
    r = int(rgb[0] * (1 - factor))
    g = int(rgb[1] * (1 - factor))
    b = int(rgb[2] * (1 - factor))
    return _rgb_to_hex((r, g, b))


# ---------------------------------------------------------------------------
# Color derivation: base color → fill / stroke / text
# ---------------------------------------------------------------------------
_FILL_FACTOR = 0.75  # lighten base → fill background
_TEXT_FACTOR = 0.4  # darken base → text foreground


def _build_emphasis(
    base_name: str,
    fill_factor: float = _FILL_FACTOR,
    text_factor: float = _TEXT_FACTOR,
) -> Dict[str, str]:
    """Derive fill/stroke/text from a SCITEX base color."""
    rgb = _SCITEX_RGB[base_name]
    return {
        "fill": _lighten(rgb, fill_factor),
        "stroke": _rgb_to_hex(rgb),
        "text": _darken(rgb, text_factor),
    }


# Semantic emphasis styles — all derived from SCITEX base colors
EMPHASIS_COLORS: Dict[str, Dict[str, str]] = {
    "normal": _build_emphasis("gray", fill_factor=0.85),
    "primary": _build_emphasis("blue"),
    "success": _build_emphasis("green"),
    "warning": _build_emphasis("yellow"),
    "muted": _build_emphasis("gray", fill_factor=0.88, text_factor=0.3),
}

# Edge styles (neutral gray tones from SCITEX gray)
EDGE_STYLES = {
    "solid": {"linestyle": "-", "color": _darken(_SCITEX_RGB["gray"], 0.25)},
    "dashed": {"linestyle": "--", "color": _rgb_to_hex(_SCITEX_RGB["gray"])},
    "dotted": {"linestyle": ":", "color": _lighten(_SCITEX_RGB["gray"], 0.25)},
}

# Font configuration.
#
# These values are the FALLBACK used only when no figrecipe style is active
# (e.g. ``fr.load_style(None)``) or when the style cannot be read. When a style
# IS active, ``resolve_font_config()`` overrides the *_size keys from the active
# style's font points so diagrams match regular figures (single source of
# truth: ``styles/presets/*.yaml`` via ``to_subplots_kwargs``). See that
# function for the role -> point-size mapping.
FONT_CONFIG = {
    "family": "sans-serif",
    "node_size": 9,
    "edge_label_size": 7,
    "title_size": 11,
    "weight": "normal",
}

# Emit the "no active style, using fallback fonts" warning at most once so a
# render loop does not spam the log (no-silent-fallback: still surfaced once).
_FALLBACK_WARNED = False


def resolve_font_config() -> Dict[str, object]:
    """Resolve diagram font sizes from the *active* figrecipe style.

    Diagrams share ONE source of truth with regular figures: the active style's
    font points, read via ``styles.to_subplots_kwargs()`` (the same converter
    ``ps.subplots`` consumes). Resolving here -- at render time -- means a
    diagram built under SCITEX inherits SCITEX font sizes, and changing
    ``SCITEX.yaml`` (or loading another preset) moves both diagrams and figures.

    Role -> style point-size mapping (SCITEX defaults in parentheses):

    - ``title_size``      <- ``fonts_title_pt``       (8) diagram + box titles
    - ``node_size``       <- ``fonts_axis_label_pt``  (7) box/node label text
    - ``edge_label_size`` <- ``fonts_legend_pt``      (6) arrow/edge labels

    ``edge_label_size`` uses ``legend_pt`` (not ``tick_label_pt``) so edge
    labels stay one step smaller than node text, preserving the original visual
    hierarchy (edge < node) now that node text shrank from 9 to 7.

    ``family`` and ``weight`` are not style-driven and keep their FONT_CONFIG
    values (the style's ``fonts.family`` governs rcParams already; diagram text
    inherits it through matplotlib unless explicitly set).

    Returns
    -------
    dict
        A copy of FONT_CONFIG with the ``*_size`` keys overridden from the
        active style. When no style is active (or it cannot be read) the
        FONT_CONFIG fallback values are returned unchanged (warned once).
    """
    global _FALLBACK_WARNED

    config = dict(FONT_CONFIG)

    try:
        from ...styles._kwargs_converter import to_subplots_kwargs
        from ...styles._style_loader import _STYLE_CACHE
    except Exception:  # pragma: no cover - styles package always importable
        return config

    # No style loaded -> intentional fallback to FONT_CONFIG constants. Surface
    # it once instead of silently shrinking/keeping the wrong size.
    if _STYLE_CACHE is None:
        if not _FALLBACK_WARNED:
            import warnings

            warnings.warn(
                "No figrecipe style active; diagram fonts use FONT_CONFIG "
                "fallback sizes. Call fr.load_style('SCITEX') so diagram fonts "
                "match figures.",
                UserWarning,
                stacklevel=2,
            )
            _FALLBACK_WARNED = True
        return config

    kwargs = to_subplots_kwargs(_STYLE_CACHE)
    config["title_size"] = kwargs["fonts_title_pt"]
    config["node_size"] = kwargs["fonts_axis_label_pt"]
    config["edge_label_size"] = kwargs["fonts_legend_pt"]
    return config


# Named colors (hex) for direct access
COLORS = {name: _rgb_to_hex(rgb) for name, rgb in _SCITEX_RGB.items()}
COLORS_LIGHT = {name: _lighten(rgb, _FILL_FACTOR) for name, rgb in _SCITEX_RGB.items()}


def get_emphasis_style(emphasis: str) -> Dict[str, str]:
    """Get fill, stroke, text colors for an emphasis level or color name.

    Parameters
    ----------
    emphasis : str
        Semantic: "normal", "primary", "success", "warning", "muted"
        Color name: "blue", "red", "green", "yellow", "purple", etc.

    Returns
    -------
    dict
        Dictionary with 'fill', 'stroke', 'text' color values.
    """
    if emphasis in EMPHASIS_COLORS:
        return EMPHASIS_COLORS[emphasis]
    # Allow direct SCITEX color names (e.g., emphasis="blue", "red")
    if emphasis in _SCITEX_RGB:
        return _build_emphasis(emphasis)
    return EMPHASIS_COLORS["normal"]


def get_edge_style(style: str) -> Dict[str, str]:
    """Get linestyle and color for an edge style.

    Parameters
    ----------
    style : str
        Named: "solid", "dashed", "dotted"
        Matplotlib: "-", "--", ":", "-."

    Returns
    -------
    dict
        Dictionary with 'linestyle' and 'color' values.
    """
    if style in EDGE_STYLES:
        return EDGE_STYLES[style]
    # Accept matplotlib linestyle strings directly
    _MPL_ALIASES = {"--": "dashed", ":": "dotted", "-.": "dashed", "-": "solid"}
    if style in _MPL_ALIASES:
        return EDGE_STYLES[_MPL_ALIASES[style]]
    return EDGE_STYLES["solid"]


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to RGB tuple (0-1 range)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def get_auto_colors(n: int) -> List[str]:
    """Generate n distinct colors from SCITEX palette.

    Parameters
    ----------
    n : int
        Number of colors needed.

    Returns
    -------
    list
        List of hex color strings.
    """
    order = [
        "blue",
        "red",
        "green",
        "yellow",
        "purple",
        "lightblue",
        "orange",
        "pink",
        "navy",
        "brown",
    ]
    return [COLORS[order[i % len(order)]] for i in range(n)]


__all__ = [
    "COLORS",
    "COLORS_LIGHT",
    "EMPHASIS_COLORS",
    "EDGE_STYLES",
    "FONT_CONFIG",
    "resolve_font_config",
    "get_emphasis_style",
    "get_edge_style",
    "hex_to_rgb",
    "get_auto_colors",
]

# EOF
