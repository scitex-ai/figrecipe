#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: figrecipe/presets/_scitex_style.py

"""Flat ``SCITEX_STYLE`` preset (single source of truth: ``SCITEX_STYLE.yaml``).

This module owns the flat dict of ``subplots()`` kwargs that scitex.plt used to
build via ``scitex.plt.styles.presets``. It is reimplemented here with PyYAML
only (no scitex.io / scitex.config dependency) so figrecipe stays standalone.

Priority cascade for each value: direct -> env (SCITEX_PLT_*) -> yaml -> default.

Names exposed (mirroring scitex.plt.presets):
    SCITEX_STYLE, STYLE, load_style, save_style, set_style, get_style,
    resolve_style_value, get_default_dpi, get_display_dpi, get_preview_dpi,
    DPI_SAVE, DPI_DISPLAY, DPI_PREVIEW
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

_STYLE_FILE = Path(__file__).parent / "SCITEX_STYLE.yaml"
_ENV_PREFIX = "SCITEX_PLT_"

_active_style: Optional[Dict[str, Any]] = None  # user-set override
_yaml_cache: Optional[Dict[str, Any]] = None
_yaml_cache_path: Optional[Path] = None

# Fallback DPI values (only used if config unavailable)
_FALLBACK_DPI_SAVE = 300
_FALLBACK_DPI_DISPLAY = 100
_FALLBACK_DPI_PREVIEW = 150


def _load_yaml(yaml_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load (and cache) the nested YAML style file."""
    global _yaml_cache, _yaml_cache_path
    path = Path(yaml_path) if yaml_path else _STYLE_FILE
    if _yaml_cache is None or path != _yaml_cache_path:
        with open(path) as f:
            _yaml_cache = yaml.safe_load(f) or {}
        _yaml_cache_path = path
    return _yaml_cache


def _yaml_get(data: Dict[str, Any], dotted_key: str) -> Any:
    """Resolve a 'section.key' path against the nested YAML dict."""
    section, _, key = dotted_key.partition(".")
    sub = data.get(section)
    if isinstance(sub, dict):
        return sub.get(key)
    return None


def _coerce(value: Any, type_: type) -> Any:
    if value is None:
        return None
    if type_ is bool:
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    return type_(value)


def resolve_style_value(
    key: str,
    direct_val: Any = None,
    default: Any = None,
    type: type = float,  # noqa: A002 - keep scitex-compatible signature
    yaml_path: Optional[Union[str, Path]] = None,
) -> Any:
    """Resolve value with priority: direct -> env -> yaml -> default.

    Key format: 'axes.width_mm' (dots for YAML hierarchy). The env var is
    ``SCITEX_PLT_AXES_WIDTH_MM`` (prefix + key with dots->underscores, uppercased).
    """
    if direct_val is not None:
        return _coerce(direct_val, type)

    env_key = _ENV_PREFIX + key.replace(".", "_").upper()
    if env_key in os.environ:
        return _coerce(os.environ[env_key], type)

    yaml_val = _yaml_get(_load_yaml(Path(yaml_path) if yaml_path else None), key)
    if yaml_val is not None:
        return _coerce(yaml_val, type)

    return default if default is None else _coerce(default, type)


# =============================================================================
# DPI resolution
# =============================================================================
def get_default_dpi() -> int:
    """Default DPI for saving/publication (yaml -> env -> 300)."""
    return int(resolve_style_value("output.dpi", None, _FALLBACK_DPI_SAVE, int))


def get_display_dpi() -> int:
    """DPI for screen display (~1/3 of save DPI, min 100)."""
    return max(_FALLBACK_DPI_DISPLAY, get_default_dpi() // 3)


def get_preview_dpi() -> int:
    """DPI for editor previews (1/2 of save DPI, clamped 100-200)."""
    return max(_FALLBACK_DPI_DISPLAY, min(200, get_default_dpi() // 2))


DPI_SAVE = _FALLBACK_DPI_SAVE
DPI_DISPLAY = _FALLBACK_DPI_DISPLAY
DPI_PREVIEW = _FALLBACK_DPI_PREVIEW


# =============================================================================
# Flat-key <-> hierarchical mapping (single source of truth)
# =============================================================================
# flat_key -> (yaml_dotted_key, default, type)
_FLAT_SPEC = [
    ("axes_width_mm", "axes.width_mm", 40, float),
    ("axes_height_mm", "axes.height_mm", 28, float),
    ("axes_thickness_mm", "axes.thickness_mm", 0.2, float),
    ("margin_left_mm", "margins.left_mm", 20, float),
    ("margin_right_mm", "margins.right_mm", 20, float),
    ("margin_bottom_mm", "margins.bottom_mm", 20, float),
    ("margin_top_mm", "margins.top_mm", 20, float),
    ("space_w_mm", "spacing.horizontal_mm", 8, float),
    ("space_h_mm", "spacing.vertical_mm", 10, float),
    ("tick_length_mm", "ticks.length_mm", 0.8, float),
    ("tick_thickness_mm", "ticks.thickness_mm", 0.2, float),
    ("n_ticks", "ticks.n_ticks", 4, int),
    ("trace_thickness_mm", "lines.trace_mm", 0.2, float),
    ("errorbar_thickness_mm", "lines.errorbar_mm", 0.2, float),
    ("errorbar_cap_width_mm", "lines.errorbar_cap_mm", 0.8, float),
    ("bar_edge_thickness_mm", "lines.bar_edge_mm", 0.2, float),
    ("kde_line_thickness_mm", "lines.kde_mm", 0.2, float),
    ("scatter_size_mm", "markers.scatter_mm", 0.8, float),
    ("marker_size_mm", "markers.size_mm", 0.8, float),
    ("font_family", "fonts.family", "Arial", str),
    ("axis_font_size_pt", "fonts.axis_label_pt", 7, float),
    ("tick_font_size_pt", "fonts.tick_label_pt", 7, float),
    ("title_font_size_pt", "fonts.title_pt", 8, float),
    ("suptitle_font_size_pt", "fonts.suptitle_pt", 8, float),
    ("legend_font_size_pt", "fonts.legend_pt", 6, float),
    ("annotation_font_size_pt", "fonts.annotation_pt", 6, float),
    ("label_pad_pt", "padding.label_pt", 0.5, float),
    ("tick_pad_pt", "padding.tick_pt", 2.0, float),
    ("title_pad_pt", "padding.title_pt", 1.0, float),
    ("dpi", "output.dpi", 300, int),
    ("transparent", "output.transparent", True, bool),
    ("auto_scale_axes", "behavior.auto_scale_axes", True, bool),
]

_FLAT_TO_HIERARCHICAL = {
    flat: tuple(dotted.split(".")) for flat, dotted, _, _ in _FLAT_SPEC
}


def load_style(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load the flat style dict (subplots kwargs) from YAML."""
    yaml_path = Path(path) if path else None
    style = {
        flat: resolve_style_value(dotted, None, default, type_, yaml_path)
        for flat, dotted, default, type_ in _FLAT_SPEC
    }
    style["mode"] = "publication"
    return style


def get_style() -> Dict[str, Any]:
    """Get the current active style (active override -> env -> yaml -> default)."""
    base = load_style()
    if _active_style:
        base.update(_active_style)
    return base


def set_style(style_dict: Optional[Dict[str, Any]] = None) -> None:
    """Set the active style globally. Pass None to reset to defaults."""
    global _active_style, SCITEX_STYLE, STYLE
    _active_style = style_dict
    SCITEX_STYLE = get_style()
    STYLE = SCITEX_STYLE


def _flat_to_hierarchical(style: Dict[str, Any]) -> Dict[str, Any]:
    """Convert flat style dict back to nested YAML structure."""
    result: Dict[str, Any] = {}
    for flat_key, value in style.items():
        if flat_key in _FLAT_TO_HIERARCHICAL:
            section, key = _FLAT_TO_HIERARCHICAL[flat_key]
            result.setdefault(section, {})[key] = value
    return result


def save_style(path: Union[str, Path], style: Optional[Dict[str, Any]] = None) -> Path:
    """Export the (active or given) flat style to a YAML/JSON file."""
    path = Path(path)
    style = style or get_style()
    hierarchical = _flat_to_hierarchical(style)
    if path.suffix.lower() == ".json":
        import json

        with open(path, "w") as f:
            json.dump(hierarchical, f, indent=2)
    else:
        with open(path, "w") as f:
            yaml.safe_dump(hierarchical, f, sort_keys=False)
    return path


SCITEX_STYLE = load_style()
STYLE = SCITEX_STYLE

__all__ = [
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
