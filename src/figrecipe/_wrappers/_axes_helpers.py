#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions for RecordingAxes."""

from typing import Any, Dict, Optional

# Methods that support clip_on parameter (plotting methods, not decoration methods)
CLIP_ON_SUPPORTED_METHODS = {
    "plot",
    "scatter",
    "bar",
    "barh",
    "hist",
    "step",
    "fill",
    "fill_between",
    "fill_betweenx",
    "errorbar",
    "axhline",
    "axvline",
    "axhspan",
    "axvspan",
    "hlines",
    "vlines",
    "quiver",
    "hexbin",
    "pcolormesh",
    "pcolor",
    "imshow",
    "matshow",
    "spy",
    "tripcolor",
    "tricontour",
    "tricontourf",
    "triplot",
    "stackplot",
    "stairs",
    "broken_barh",
    "eventplot",
    "ecdf",
    "magnitude_spectrum",
    "angle_spectrum",
    "phase_spectrum",
    "psd",
    "csd",
    "cohere",
    "specgram",
    "acorr",
    "xcorr",
    # NOTE: stem, streamplot, and contour are NOT included - they do not support clip_on
}


def inject_clip_on_from_style(kwargs: dict, method_name: str = None) -> dict:
    """Inject clip_on=False if style dictates (figrecipe handles cropping).

    Parameters
    ----------
    kwargs : dict
        Keyword arguments to augment.
    method_name : str, optional
        Name of the plotting method. If provided, only inject for methods
        that support clip_on parameter.

    Returns
    -------
    dict
        Updated kwargs with clip_on=False if applicable.
    """
    from ..styles._style_loader import _STYLE_CACHE

    # Only inject for methods that support clip_on
    if method_name is not None and method_name not in CLIP_ON_SUPPORTED_METHODS:
        return kwargs

    if "clip_on" not in kwargs and _STYLE_CACHE is not None:
        behavior = _STYLE_CACHE.get("behavior", {})
        if behavior.get("clip_on") is False:
            kwargs["clip_on"] = False
    return kwargs


def _resolve_signal_linewidth_token(kwargs: dict) -> dict:
    """Resolve the special ``linewidth="signal"`` / ``lw="signal"`` token.

    ``"signal"`` maps to the SCITEX style's thin signal-trace width
    (``lines.signal_linewidth_mm``, ~0.12mm) converted to points. Numeric
    linewidths pass through untouched. The token is resolved to a number
    *before* the call is recorded, so recipe replay stays faithful (no
    figrecipe-specific token leaks into the recorded kwargs).
    """
    from .._utils._units import mm_to_pt
    from ..styles._style_loader import _STYLE_CACHE

    for key in ("linewidth", "lw"):
        if kwargs.get(key) == "signal":
            signal_mm = 0.12
            if _STYLE_CACHE is not None:
                lines = _STYLE_CACHE.get("lines", {})
                signal_mm = lines.get(
                    "signal_linewidth_mm", lines.get("trace_mm", 0.12)
                )
            kwargs[key] = mm_to_pt(signal_mm)
    return kwargs


def inject_method_defaults(kwargs: dict, method_name: str) -> dict:
    """Inject method-specific defaults from SCITEX style.

    Parameters
    ----------
    kwargs : dict
        Keyword arguments to augment.
    method_name : str
        Name of the plotting method.

    Returns
    -------
    dict
        Updated kwargs with style defaults applied.
    """
    from ..styles._style_loader import _STYLE_CACHE

    # Special linewidth token works regardless of whether a style is loaded
    # (falls back to 0.12mm) and applies to every wrapped plotting method.
    kwargs = _resolve_signal_linewidth_token(kwargs)

    if _STYLE_CACHE is None:
        return kwargs

    if method_name == "fill_between" or method_name == "fill_betweenx":
        fb_style = _STYLE_CACHE.get("fill_between", {})
        if "edgecolor" not in kwargs:
            edgecolor = fb_style.get("edgecolor", "none")
            kwargs["edgecolor"] = edgecolor
        if "alpha" not in kwargs:
            alpha = fb_style.get("alpha")
            if alpha is not None:
                kwargs["alpha"] = alpha

    elif method_name == "eventplot":
        ep_style = _STYLE_CACHE.get("eventplot", {})
        from .._utils._units import mm_to_pt

        if "linewidths" not in kwargs:
            lw_mm = ep_style.get("linewidth_mm", 0.12)
            kwargs["linewidths"] = mm_to_pt(lw_mm)
        if "linelengths" not in kwargs:
            ll = ep_style.get("linelength", 0.5)
            kwargs["linelengths"] = ll

    return kwargs


def args_have_fmt_color(args: tuple) -> bool:
    """Check if args contain a matplotlib fmt string with color specifier."""
    color_codes = set("bgrcmykw")
    for arg in args:
        if isinstance(arg, str) and len(arg) >= 1 and len(arg) <= 4:
            if arg[0] in color_codes:
                return True
    return False


def extract_color_from_result(method_name: str, result) -> Optional[str]:
    """Extract actual color used from plot result."""
    try:
        if method_name == "plot":
            if result and hasattr(result[0], "get_color"):
                return result[0].get_color()
        elif method_name == "scatter":
            if hasattr(result, "get_facecolor"):
                fc = result.get_facecolor()
                if len(fc) > 0:
                    import matplotlib.colors as mcolors

                    return mcolors.to_hex(fc[0])
        elif method_name in ("bar", "barh"):
            if hasattr(result, "patches") and result.patches:
                fc = result.patches[0].get_facecolor()
                import matplotlib.colors as mcolors

                return mcolors.to_hex(fc)
        elif method_name == "step":
            if result and hasattr(result[0], "get_color"):
                return result[0].get_color()
        elif method_name == "ecdf":
            if result and hasattr(result, "get_color"):
                return result.get_color()
        elif method_name == "fill_between":
            if hasattr(result, "get_facecolor"):
                fc = result.get_facecolor()
                if len(fc) > 0:
                    import matplotlib.colors as mcolors

                    return mcolors.to_hex(fc[0])
        elif method_name == "stem":
            # StemContainer has markerline, stemlines, baseline
            if hasattr(result, "markerline"):
                color = result.markerline.get_color()
                import matplotlib.colors as mcolors

                return mcolors.to_hex(color)
    except Exception:
        pass
    return None


def process_result_refs_in_args(
    args: tuple,
    method_name: str,
    result_refs: Dict[int, str],
    referencing_methods: set,
) -> tuple:
    """Process args to replace matplotlib objects with references."""
    if method_name not in referencing_methods:
        return args

    import builtins

    processed = []
    for arg in args:
        obj_id = builtins.id(arg)
        if obj_id in result_refs:
            processed.append({"__ref__": result_refs[obj_id]})
        else:
            processed.append(arg)
    return tuple(processed)


def record_call_with_color_capture(
    recorder,
    position: tuple,
    method_name: str,
    args: tuple,
    kwargs: dict,
    result,
    call_id: Optional[str],
    result_refs: Dict[int, str],
    referencing_methods: set,
    referenceable_methods: set,
) -> Any:
    """Record a call with color capture and result reference handling."""
    recorded_kwargs = kwargs.copy()

    # Capture colors for methods using color cycle
    if method_name in (
        "plot",
        "scatter",
        "bar",
        "barh",
        "step",
        "ecdf",
        "fill_between",
        "stem",
    ):
        has_fmt_color = args_have_fmt_color(args)
        if (
            "color" not in recorded_kwargs
            and "c" not in recorded_kwargs
            and not has_fmt_color
        ):
            actual_color = extract_color_from_result(method_name, result)
            if actual_color is not None:
                recorded_kwargs["color"] = actual_color

        if method_name == "fill_between" and "edgecolor" not in recorded_kwargs:
            if hasattr(result, "get_edgecolor"):
                ec = result.get_edgecolor()
                if len(ec) == 0:
                    recorded_kwargs["edgecolor"] = "none"

    # Process args for result references
    processed_args = process_result_refs_in_args(
        args, method_name, result_refs, referencing_methods
    )

    call_record = recorder.record_call(
        ax_position=position,
        method_name=method_name,
        args=processed_args,
        kwargs=recorded_kwargs,
        call_id=call_id,
    )

    # Store result reference if applicable
    if method_name in referenceable_methods:
        import builtins

        result_refs[builtins.id(result)] = call_record.id

    return call_record


__all__ = [
    "inject_clip_on_from_style",
    "inject_method_defaults",
    "args_have_fmt_color",
    "extract_color_from_result",
    "process_result_refs_in_args",
    "record_call_with_color_capture",
]

# EOF
