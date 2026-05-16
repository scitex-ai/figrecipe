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


def _record_separate_legend(ax, kwargs: dict) -> None:
    """Capture handles + labels onto fig._separate_legend_params.

    Implements the protocol that
    :func:`scitex.io._save_modules._legends.save_separate_legends`
    consumes — at save time, that function writes the legend to a
    standalone file alongside the main figure.
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
            "axis_id": getattr(ax, "_id", None) or hash(ax),
            "figsize": sep_kw.pop("figsize", (4, 2)),
            "frameon": sep_kw.pop("frameon", True),
            "fancybox": sep_kw.pop("fancybox", False),
            "shadow": sep_kw.pop("shadow", False),
            "kwargs": sep_kw,
        }
    )


def _resolve_loc_kwargs(ax, kwargs: dict) -> None:
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
            _record_separate_legend(ax, kwargs)
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


def _record_legend_call(recorder, position, args, kwargs, call_id) -> None:
    """Record the legend call into the recorder for later reproduction."""
    record_kwargs = dict(kwargs)
    if "handles" in record_kwargs:
        handles = record_kwargs.pop("handles")
        handle_specs = []
        for h in handles:
            spec: dict[str, Any] = {"label": h.get_label()}
            if hasattr(h, "get_facecolor"):
                spec["facecolor"] = list(h.get_facecolor())
            if hasattr(h, "get_edgecolor"):
                spec["edgecolor"] = list(h.get_edgecolor())
            handle_specs.append(spec)
        record_kwargs["_handle_specs"] = handle_specs
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

        # Step 2: resolve figrecipe-extended `loc=` strings.
        _resolve_loc_kwargs(recording_ax._ax, kwargs)

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
