#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record ``ax.add_patch()`` so patches round-trip through a recipe.

A patch is a live matplotlib object, so it is decomposed into a
YAML-serializable ``patch_spec`` (type + geometry + style) at record time and
rebuilt on replay (see ``figrecipe/_reproducer/_replay_patches.py``).
Unsupported patch types FAIL LOUD at call time rather than being silently
dropped (which would make the figure fail save-time reproducibility).
"""

from typing import Any, Dict

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

# Geometry-clean patch types supported for round-trip. Extend by adding a
# branch in extract_patch_spec() + _replay_patches.reconstruct_patch().
SUPPORTED_PATCH_TYPES = (
    "Rectangle",
    "Circle",
    "Ellipse",
    "Polygon",
    "FancyArrowPatch",
)

# facecolor/edgecolor are captured as RGBA hex (alpha folded in), so the
# patch-level alpha is intentionally NOT captured separately to avoid
# double-application (facecolor_alpha * patch_alpha) on replay.
_STYLE_ATTRS = ("facecolor", "edgecolor", "linewidth", "linestyle", "hatch", "zorder")


def _serialize_transform(patch) -> str:
    """Map a patch's transform to a portable marker (data/axes/figure)."""
    ax = getattr(patch, "axes", None)
    transform = patch.get_transform()
    if ax is not None:
        if transform is ax.transData:
            return "data"
        if transform is ax.transAxes:
            return "axes"
        fig = getattr(ax, "figure", None)
        if fig is not None and transform is fig.transFigure:
            return "figure"
    # transAxes reprs as "BboxTransformTo(...)"; treat as the axes marker.
    if "BboxTransformTo" in repr(transform):
        return "axes"
    return "data"


def _style_of(patch) -> Dict[str, Any]:
    style: Dict[str, Any] = {}
    for attr in _STYLE_ATTRS:
        getter = getattr(patch, f"get_{attr}", None)
        if getter is None:
            continue
        value = getter()
        if value is None:
            continue
        if attr in ("facecolor", "edgecolor"):
            try:
                value = mcolors.to_hex(value, keep_alpha=True)
            except (ValueError, TypeError):
                pass
        elif attr in ("linewidth", "zorder"):
            value = float(value)
        style[attr] = value
    style["transform"] = _serialize_transform(patch)
    return style


def _registered_style_name(style_obj, registry) -> str:
    """Return the registered short name (e.g. ``'-|>'``, ``'arc3'``) for an
    ArrowStyle/ConnectionStyle instance. FAIL LOUD on an unregistered style
    rather than silently dropping it.
    """
    for name, cls in getattr(registry, "_style_list", {}).items():
        if type(style_obj) is cls:
            return name
    raise ValueError(
        f"figrecipe cannot record {registry.__name__} "
        f"{type(style_obj).__name__!r} for reproduction. Use a standard named "
        f"style, or draw the arrow via annotate(arrowprops=...) which is recorded."
    )


def _connectionstyle_string(style_obj) -> str:
    """Serialize a ConnectionStyle to ``'name,param=value,...'``.

    A ConnectionStyle's public numeric attrs map straight back to constructor
    params (``Arc3.rad``, ``Arc.armA/armB/rad``, ``Angle.angleA/angleB``), so
    ``rad`` and friends round-trip faithfully. The candidate string is
    validated by re-parsing; a non-standard set falls back to the base named
    style (which always reconstructs) rather than raising on a valid figure.
    """
    name = _registered_style_name(style_obj, mpatches.ConnectionStyle)
    params = {
        key: float(val)
        for key, val in vars(style_obj).items()
        if not key.startswith("_")
        and isinstance(val, (int, float))
        and not isinstance(val, bool)
    }
    if not params:
        return name
    candidate = name + "," + ",".join(f"{k}={v}" for k, v in sorted(params.items()))
    try:
        mpatches.ConnectionStyle(candidate)
    except (ValueError, TypeError):
        return name
    return candidate


def _fancyarrow_spec(patch, style: Dict[str, Any]) -> Dict[str, Any]:
    """Decompose a FancyArrowPatch (posA/posB form) into a serializable spec.

    The arrowstyle is stored by its registered name only: the class identity
    already encodes the head shape + filled/open variant, and overall size is
    carried by ``mutation_scale``. Non-default per-head geometry (custom
    ``head_length``/``head_width``) is intentionally not captured -- it is rare
    for leader arrows and would pollute the spec with base-class attrs that are
    invalid params for the named style.
    """
    pos = getattr(patch, "_posA_posB", None)
    if not pos or pos[0] is None or pos[1] is None:
        raise ValueError(
            "figrecipe cannot record a path-based FancyArrowPatch (no posA/posB) "
            "for reproduction. Construct it with posA/posB, or draw the arrow via "
            "annotate(arrowprops=...) which figrecipe records."
        )
    (ax0, ay0), (ax1, ay1) = pos
    return {
        "type": "FancyArrowPatch",
        "posA": [float(ax0), float(ay0)],
        "posB": [float(ax1), float(ay1)],
        "arrowstyle": _registered_style_name(
            patch.get_arrowstyle(), mpatches.ArrowStyle
        ),
        "connectionstyle": _connectionstyle_string(patch.get_connectionstyle()),
        "mutation_scale": float(patch.get_mutation_scale()),
        "style": style,
    }


def extract_patch_spec(patch) -> Dict[str, Any]:
    """Decompose a matplotlib patch into a serializable spec.

    Raises ValueError for unsupported patch types (FAIL LOUD).
    """
    style = _style_of(patch)
    # Circle subclasses Ellipse, so it MUST be checked first.
    if isinstance(patch, mpatches.Circle):
        cx, cy = patch.center
        return {
            "type": "Circle",
            "center": [float(cx), float(cy)],
            "radius": float(patch.radius),
            "style": style,
        }
    if isinstance(patch, mpatches.Ellipse):
        cx, cy = patch.center
        return {
            "type": "Ellipse",
            "center": [float(cx), float(cy)],
            "width": float(patch.width),
            "height": float(patch.height),
            "angle": float(patch.angle),
            "style": style,
        }
    if isinstance(patch, mpatches.Rectangle):
        x, y = patch.get_xy()
        return {
            "type": "Rectangle",
            "xy": [float(x), float(y)],
            "width": float(patch.get_width()),
            "height": float(patch.get_height()),
            "angle": float(patch.get_angle()),
            "style": style,
        }
    if isinstance(patch, mpatches.Polygon):
        xy = patch.get_xy()
        verts = xy.tolist() if hasattr(xy, "tolist") else [list(p) for p in xy]
        return {
            "type": "Polygon",
            "xy": [[float(a), float(b)] for a, b in verts],
            "closed": bool(patch.get_closed()),
            "style": style,
        }
    # FancyArrowPatch (add_patch path, e.g. adjustText leaders). The
    # annotate() path already round-trips; this closes the add_patch gap so
    # standalone arrows replay too. Path-based arrows (no posA/posB) FAIL LOUD.
    if isinstance(patch, mpatches.FancyArrowPatch):
        return _fancyarrow_spec(patch, style)
    raise ValueError(
        f"figrecipe cannot record patch type {type(patch).__name__!r} for "
        f"reproduction (it would be dropped on replay). Supported: "
        f"{', '.join(SUPPORTED_PATCH_TYPES)}. Add a branch in "
        f"_wrappers/_axes_patches.py:extract_patch_spec() to support it."
    )


def build_add_patch_wrapper(recording_axes):
    """Build the recording wrapper for ``RecordingAxes.add_patch``."""

    def add_patch(patch, *, id=None, track=True, **kwargs):
        from ._axes_helpers import record_call_with_color_capture

        result = recording_axes._ax.add_patch(patch)
        if recording_axes._track and track:
            # extract_patch_spec FAILS LOUD here on unsupported types, so the
            # author learns at call time that the patch will not round-trip.
            record_kwargs = {"patch_spec": extract_patch_spec(patch)}
            record_kwargs.update(kwargs)
            record_call_with_color_capture(
                recording_axes._recorder,
                recording_axes._position,
                "add_patch",
                (),
                record_kwargs,
                result,
                id,
                recording_axes._result_refs,
                recording_axes._RESULT_REFERENCING_METHODS,
                recording_axes._RESULT_REFERENCEABLE_METHODS,
            )
        return result

    return add_patch


__all__ = ["extract_patch_spec", "build_add_patch_wrapper", "SUPPORTED_PATCH_TYPES"]
