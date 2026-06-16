#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legend wrapper for RecordingAxes.

Extracted from `_axes.py` to keep the per-method wrapper file
focused. The wrapper:

  1. Catches the positional-string anti-pattern
     ``ax.legend('upper right')`` (matplotlib would treat the string
     as the handles arg and iterate it into per-character labels) and
     routes it to the ``loc=`` kwarg.
  2. Resolves figrecipe-extended ``loc`` strings (the twelve
     ``outer …`` variants + ``'separate'``) before matplotlib sees
     them. ``outer …`` translate to ``(loc, bbox_to_anchor)`` pairs;
     ``'separate'`` flags the legend for save-time extraction (per
     :func:`scitex.io._save_modules._legends.save_separate_legends`).
  3. Defaults to matplotlib's ``'best'`` auto-pick when neither
     ``loc`` nor ``bbox_to_anchor`` is specified.
  4. Applies SCITEX legend frame styling (linewidth, edgecolor) on
     the resulting Legend artist.
  5. Records the call for reproduction.
"""

from __future__ import annotations

from typing import Any, Optional


def _ser_color(color: Any) -> Any:
    """Color -> YAML-serializable form (keep strings; tuples/arrays -> list)."""
    if color is None or isinstance(color, str):
        return color
    try:
        return [float(c) for c in color]
    except TypeError:
        return str(color)


def _handle_spec(handle: Any) -> dict:
    """Capture a legend handle's visual spec for faithful replay.

    Records the artist KIND (line/marker vs patch) plus its colour and marker
    so the composed legend reproduces the original swatch -- colour AND shape --
    instead of a grey rectangle. Live artist handles are not YAML-serializable,
    so only this semantic spec is stored.
    """
    from matplotlib.lines import Line2D

    spec: dict[str, Any] = {"label": handle.get_label()}
    if isinstance(handle, Line2D):
        spec["kind"] = "line"
        spec["color"] = _ser_color(handle.get_color())
        spec["marker"] = str(handle.get_marker())
        spec["markersize"] = float(handle.get_markersize())
        spec["markerfacecolor"] = _ser_color(handle.get_markerfacecolor())
        spec["markeredgecolor"] = _ser_color(handle.get_markeredgecolor())
        spec["linestyle"] = str(handle.get_linestyle())
        spec["linewidth"] = float(handle.get_linewidth())
    else:
        spec["kind"] = "patch"
        if hasattr(handle, "get_facecolor"):
            spec["facecolor"] = _ser_color(handle.get_facecolor())
        if hasattr(handle, "get_edgecolor"):
            spec["edgecolor"] = _ser_color(handle.get_edgecolor())
    return spec


# ---------------------------------------------------------------------------
# Lookup tables — exposed at module scope so they're cheap to construct
# (don't rebuild on every legend call) and easy to test.
# ---------------------------------------------------------------------------

KNOWN_MPL_LOCS = frozenset(
    {
        "best",
        "upper right",
        "upper left",
        "lower right",
        "lower left",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    }
)

OUTER_VARIANTS = {
    # Cardinal edges (mid-anchored)
    "outer right": {"loc": "center left", "bbox_to_anchor": (1.02, 0.5)},
    "outer left": {"loc": "center right", "bbox_to_anchor": (-0.02, 0.5)},
    "outer top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.02)},
    "outer bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
    # Corner anchored, right side
    "outer upper right": {"loc": "upper left", "bbox_to_anchor": (1.02, 1.0)},
    "outer lower right": {"loc": "lower left", "bbox_to_anchor": (1.02, 0.0)},
    # Corner anchored, left side
    "outer upper left": {"loc": "upper right", "bbox_to_anchor": (-0.02, 1.0)},
    "outer lower left": {"loc": "lower right", "bbox_to_anchor": (-0.02, 0.0)},
    # Edge-centered above/below (synonyms of outer top / outer bottom)
    "outer upper center": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.02)},
    "outer lower center": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
}

# Order-insensitive aliases — accept "outer right upper" etc.
OUTER_ALIASES = {
    "outer right upper": "outer upper right",
    "outer right lower": "outer lower right",
    "outer left upper": "outer upper left",
    "outer left lower": "outer lower left",
    "outer center upper": "outer upper center",
    "outer center lower": "outer lower center",
}


def _normalize_loc(s: str) -> str:
    """Collapse whitespace + lowercase + alias-resolve a loc string."""
    norm = " ".join(s.lower().split())
    return OUTER_ALIASES.get(norm, norm)


def _route_positional_loc(args: tuple, kwargs: dict) -> tuple:
    """Anti-pattern catcher for ``ax.legend('upper right')``.

    Routes a single string positional that looks like a known loc value
    over to ``kwargs['loc']`` so matplotlib doesn't treat it as
    ``handles``. Returns the (possibly empty) updated args tuple.
    """
    if len(args) == 1 and isinstance(args[0], str) and "loc" not in kwargs:
        norm = _normalize_loc(args[0])
        if norm in KNOWN_MPL_LOCS or norm.startswith("outer") or norm == "separate":
            kwargs["loc"] = args[0]
            return ()
    return args


def _stable_axis_id(ax, axis_id=None) -> str:
    """Deterministic id for the separate-legend filename.

    The downstream saver (scitex.io) builds the legend filename as
    ``<figstem>_<axis_id>_legend.png``. Previously ``axis_id`` fell back
    to ``hash(ax)``, which is non-deterministic across processes/renders,
    so every render emitted a NEW file with a different id. We instead
    derive a STABLE id from the axes' grid position (row, col), so the
    same panel always writes the same ``_legend.png`` and overwrites in
    place. Multiple distinct axes still get distinct (stable) ids.
    """
    if axis_id is not None:
        return str(axis_id)
    pos = getattr(ax, "_id", None)
    if pos is not None:
        return str(pos)
    # Fallback: position within the figure's axes list (stable per figure).
    try:
        fig = ax.get_figure()
        return f"ax{fig.axes.index(ax)}"
    except (ValueError, AttributeError):
        return "ax0"


def _record_separate_legend(ax, kwargs: dict, axis_id=None) -> None:
    """Capture handles + labels onto fig._separate_legend_params.

    Implements the protocol that
    :func:`scitex.io._save_modules._legends.save_separate_legends`
    consumes — at save time, that function writes the legend to a
    standalone file alongside the main figure. ``axis_id`` is a STABLE
    identifier (derived from the panel's grid position) so the legend
    filename is deterministic and overwrites in place across renders.
    """
    h_kw = kwargs.pop("handles", None)
    l_kw = kwargs.pop("labels", None)
    if h_kw is None or l_kw is None:
        h_a, l_a = ax.get_legend_handles_labels()
        h_kw = h_kw if h_kw is not None else h_a
        l_kw = l_kw if l_kw is not None else l_a
    sep_kw = {
        k: v
        for k, v in kwargs.items()
        if k not in {"loc", "bbox_to_anchor", "borderaxespad"}
    }
    fig = ax.get_figure()
    if not hasattr(fig, "_separate_legend_params"):
        fig._separate_legend_params = []
    fig._separate_legend_params.append(
        {
            "handles": list(h_kw),
            "labels": list(l_kw),
            "axis_id": _stable_axis_id(ax, axis_id),
            "figsize": sep_kw.pop("figsize", (4, 2)),
            "frameon": sep_kw.pop("frameon", True),
            "fancybox": sep_kw.pop("fancybox", False),
            "shadow": sep_kw.pop("shadow", False),
            "kwargs": sep_kw,
        }
    )


def _resolve_loc_kwargs(ax, kwargs: dict, axis_id=None) -> None:
    """Translate figrecipe-extended loc strings to matplotlib kwargs.

    Mutates *kwargs* in place. Falls back to ``loc='best'`` when the
    caller specified neither ``loc`` nor ``bbox_to_anchor``.
    """
    user_loc = kwargs.get("loc")
    if isinstance(user_loc, str):
        norm = _normalize_loc(user_loc)
        if norm in OUTER_VARIANTS:
            if "bbox_to_anchor" not in kwargs:
                kwargs["bbox_to_anchor"] = OUTER_VARIANTS[norm]["bbox_to_anchor"]
            kwargs["loc"] = OUTER_VARIANTS[norm]["loc"]
            kwargs.setdefault("borderaxespad", 0.0)
        elif norm == "separate":
            _record_separate_legend(ax, kwargs, axis_id=axis_id)
            outer = OUTER_VARIANTS["outer right"]
            kwargs["loc"] = outer["loc"]
            kwargs["bbox_to_anchor"] = outer["bbox_to_anchor"]
            kwargs.setdefault("borderaxespad", 0.0)
    elif "loc" not in kwargs and "bbox_to_anchor" not in kwargs:
        # matplotlib auto-pick. Earlier figrecipe versions defaulted
        # to outer right; that consistently shrank wide plots via
        # constrained_layout. Defer to matplotlib's heuristic.
        kwargs["loc"] = "best"


def _apply_frame_styling(legend) -> None:
    """SCITEX-preset frame styling on a Legend artist."""
    if legend is None:
        return
    from ..styles import load_style

    style = load_style()
    legend_config = style.get("legend", {})
    frameon = legend_config.get("frameon", True)
    edge_mm = legend_config.get("edge_mm", 0.2)
    edgecolor = legend_config.get("edgecolor", "black")
    if frameon and edge_mm:
        frame = legend.get_frame()
        frame.set_linewidth(edge_mm * 72 / 25.4)  # mm → points
        if edgecolor:
            frame.set_edgecolor(edgecolor)


# Legend kwargs whose values are render-time matplotlib objects
# (artists, custom HandlerBase instances, ...) that are NOT YAML- or
# pickle-serializable. Capturing them verbatim makes the recipe dump
# raise, which previously left a 0-byte recipe on disk. We drop them
# from the recorded recipe: they affect only how the legend is drawn,
# not its semantic content (labels/handles metadata are captured
# separately via ``_handle_specs``).
_NON_SERIALIZABLE_LEGEND_KWARGS = frozenset(
    {
        "handler_map",  # {handle: HandlerBase} -> live artists + handlers
        "handles",  # handled below via _handle_specs
    }
)


def _record_legend_call(recorder, position, args, kwargs, call_id) -> None:
    """Record the legend call into the recorder for later reproduction.

    Render-time matplotlib objects (a custom ``handler_map`` of
    :class:`~matplotlib.legend_handler.HandlerBase` instances, live
    artist handles, ...) are *not* recorded verbatim: they are not
    YAML-serializable and would otherwise make the recipe dump raise.
    The legend's semantic content (handle labels + colors) is captured
    via ``_handle_specs`` instead, and a safe summary of any dropped
    ``handler_map`` is kept for debugging.
    """
    record_kwargs = dict(kwargs)

    # Capture handle metadata before dropping the live artists.
    if "handles" in record_kwargs:
        handles = record_kwargs.get("handles")
        handle_specs = [_handle_spec(h) for h in handles]
        record_kwargs["_handle_specs"] = handle_specs

    # Record that a custom handler_map was used (safe repr) but drop the
    # live, non-serializable objects so the recipe dump never breaks.
    handler_map = record_kwargs.get("handler_map")
    if handler_map:
        try:
            record_kwargs["_handler_map_summary"] = [
                type(handler).__name__ for handler in handler_map.values()
            ]
        except Exception:
            record_kwargs["_handler_map_summary"] = "custom"

    # Drop all render-time-only legend objects from the recorded recipe.
    for key in _NON_SERIALIZABLE_LEGEND_KWARGS:
        record_kwargs.pop(key, None)

    recorder.record_call(
        ax_position=position,
        method_name="legend",
        args=args,
        kwargs=record_kwargs,
        call_id=call_id,
    )


def build_legend_wrapper(recording_ax) -> Any:
    """Construct the legend() wrapper closure for a given RecordingAxes.

    This is what `RecordingAxes._create_legend_wrapper` returns: a
    callable that the user invokes as `ax.legend(...)`.
    """
    original_legend = recording_ax._ax.legend

    def wrapper(
        *args,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        # Step 1: catch the `ax.legend('upper right')` anti-pattern.
        args = _route_positional_loc(args, kwargs)

        # Step 2: resolve figrecipe-extended `loc=` strings. Pass the
        # RecordingAxes' stable grid position so a 'separate' legend gets a
        # deterministic filename (no random per-render id).
        _pos = getattr(recording_ax, "_position", None)
        _axis_id = (
            "_".join(str(p) for p in _pos) if isinstance(_pos, (tuple, list)) else _pos
        )
        _resolve_loc_kwargs(recording_ax._ax, kwargs, axis_id=_axis_id)

        # Step 3: call matplotlib.
        legend = original_legend(*args, **kwargs)

        # Step 4: apply SCITEX legend frame styling.
        _apply_frame_styling(legend)

        # Step 5: record for reproduction.
        if recording_ax._track and track:
            _record_legend_call(
                recording_ax._recorder,
                recording_ax._position,
                args,
                kwargs,
                id,
            )

        return legend

    return wrapper
