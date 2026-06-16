#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-time settings, path resolution, and transparency helpers.

Extracted from ``_save.py`` (which kept growing past the module line limit) so
that file stays a focused ``save_figure`` orchestrator. These are the small,
cohesive helpers that resolve output paths, pick the default image format / DPI
/ transparency from the active style, and temporarily force opaque patches.
``_save`` re-exports every public name here, so existing
``from .._api._save import get_save_dpi`` (etc.) imports keep working.
"""

from pathlib import Path
from typing import Optional, Tuple

# Image extensions supported for saving
IMAGE_EXTENSIONS = {
    ".png",
    ".pdf",
    ".svg",
    ".jpg",
    ".jpeg",
    ".eps",
    ".tiff",
    ".tif",
}
YAML_EXTENSIONS = {".yaml", ".yml"}


def resolve_save_paths(
    path: Path,
    image_format: Optional[str] = None,
) -> Tuple[Path, Path, str]:
    """Resolve image and YAML paths from the provided path.

    Parameters
    ----------
    path : Path
        User-provided output path.
    image_format : str, optional
        Explicit image format when path is YAML.

    Returns
    -------
    tuple
        (image_path, yaml_path, img_format)
    """
    suffix_lower = path.suffix.lower()

    if suffix_lower in IMAGE_EXTENSIONS:
        # User provided image path
        image_path = path
        yaml_path = path.with_suffix(".yaml")
        img_format = suffix_lower[1:]  # Remove leading dot
    elif suffix_lower in YAML_EXTENSIONS:
        # User provided YAML path
        yaml_path = path
        img_format = _get_default_image_format(image_format)
        image_path = path.with_suffix(f".{img_format}")
    else:
        # Unknown extension - treat as base name, add both extensions
        yaml_path = path.with_suffix(".yaml")
        img_format = _get_default_image_format(image_format)
        image_path = path.with_suffix(f".{img_format}")

    return image_path, yaml_path, img_format


def _get_default_image_format(explicit_format: Optional[str] = None) -> str:
    """Get default image format from style or fallback to png."""
    if explicit_format is not None:
        return explicit_format.lower().lstrip(".")

    # Check global style for preferred format
    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.format.lower()
        except (KeyError, AttributeError):
            pass
    return "png"


def get_save_dpi(explicit_dpi: Optional[int] = None) -> int:
    """Get DPI for saving, using style default if not specified."""
    if explicit_dpi is not None:
        return explicit_dpi

    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.dpi
        except (KeyError, AttributeError):
            pass
    return 300


def get_save_transparency() -> bool:
    """Get transparency setting from style."""
    from ..styles._style_loader import _STYLE_CACHE

    if _STYLE_CACHE is not None:
        try:
            return _STYLE_CACHE.output.transparent
        except (KeyError, AttributeError):
            pass
    return False


def _is_opaque_facecolor(facecolor) -> bool:
    """Check if facecolor is an opaque color (not transparent/none)."""
    if facecolor is None:
        return False
    if isinstance(facecolor, str):
        if facecolor.lower() in ("none", "transparent"):
            return False
    return True


def _make_patches_opaque(fig):
    """Temporarily make figure and axes patches opaque. Returns restore function."""
    original_alphas = []

    # Store and set figure patch alpha
    fig_patch = fig.fig.patch
    original_alphas.append(("fig", fig_patch.get_alpha()))
    fig_patch.set_alpha(1.0)

    # Store and set axes patch alphas
    for ax in fig.fig.get_axes():
        ax_patch = ax.patch
        original_alphas.append(("ax", ax, ax_patch.get_alpha()))
        ax_patch.set_alpha(1.0)

    def restore():
        for item in original_alphas:
            if item[0] == "fig":
                fig_patch.set_alpha(item[1])
            else:
                item[1].patch.set_alpha(item[2])

    return restore


__all__ = [
    "IMAGE_EXTENSIONS",
    "YAML_EXTENSIONS",
    "resolve_save_paths",
    "_get_default_image_format",
    "get_save_dpi",
    "get_save_transparency",
    "_is_opaque_facecolor",
    "_make_patches_opaque",
]

# EOF
