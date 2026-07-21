#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Style management API for figrecipe.

Provides style loading, unloading, and application functions.
"""

__all__ = [
    "load_style",
    "unload_style",
    "list_presets",
    "apply_style",
    "STYLE",
]


def load_style(style="SCITEX", dark=False, background=None):
    """Load style configuration and apply it globally.

    After calling this function, subsequent `subplots()` calls will
    automatically use the loaded style (fonts, colors, theme, etc.).

    Parameters
    ----------
    style : str, Path, bool, or None
        One of:
        - "SCITEX" / "FIGRECIPE": Scientific publication style (default)
        - "MATPLOTLIB": Vanilla matplotlib defaults
        - Path to custom YAML file: "/path/to/my_style.yaml"
        - None or False: Unload style (reset to matplotlib defaults)
    dark : bool, optional
        If True, apply dark theme transformation (default: False).
        Equivalent to appending "_DARK" to preset name.
    background : str, optional
        Override default background color. E.g., 'white' for opaque figures.
        Sets theme.light.figure_bg and theme.light.axes_bg.
        Use 'transparent' for transparent background.

    Returns
    -------
    DotDict or None
        Style configuration with dot-notation access.
        Returns None if style is unloaded.

    Examples
    --------
    >>> import figrecipe as fr

    >>> # Load scientific style (default)
    >>> fr.load_style()
    >>> fr.load_style("SCITEX")  # explicit

    >>> # Load with white background (override transparent default)
    >>> fr.load_style("SCITEX", background='white')

    >>> # Load dark theme
    >>> fr.load_style("SCITEX_DARK")
    >>> fr.load_style("SCITEX", dark=True)  # equivalent

    >>> # Reset to vanilla matplotlib
    >>> fr.load_style(None)    # unload
    >>> fr.load_style(False)   # unload
    >>> fr.load_style("MATPLOTLIB")  # explicit vanilla

    >>> # Access style values
    >>> style = fr.load_style("SCITEX")
    >>> style.axes.width_mm
    40
    """
    from ..styles import load_style as _load_style

    loaded = _load_style(style, dark=dark)

    if loaded is None:
        return None

    # Apply background override (figure and axes, not legend)
    if background is not None:
        theme_key = "dark" if dark else "light"
        if hasattr(loaded, "theme") and hasattr(loaded.theme, theme_key):
            theme = getattr(loaded.theme, theme_key)
            if background == "transparent":
                theme.figure_bg = "none"
                theme.axes_bg = "none"
            else:
                theme.figure_bg = background
                theme.axes_bg = background

    return loaded


def unload_style():
    """Unload the current style and reset to matplotlib defaults.

    After calling this, subsequent `subplots()` calls will use vanilla
    matplotlib behavior without FigRecipe styling.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fr.load_style("SCITEX")  # Apply scientific style
    >>> fig, ax = fr.subplots()  # Styled
    >>> fr.unload_style()        # Reset to matplotlib defaults
    >>> fig, ax = fr.subplots()  # Vanilla matplotlib
    """
    from ..styles import unload_style as _unload_style

    _unload_style()


def list_presets():
    """List available style presets.

    Returns
    -------
    list of str
        Names of available presets.

    Examples
    --------
    >>> import figrecipe as ps
    >>> ps.list_presets()
    ['MINIMAL', 'PRESENTATION', 'SCIENTIFIC']
    """
    from ..styles import list_presets as _list_presets

    return _list_presets()


def apply_style(ax, style=None):
    """Apply mm-based styling to an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes to apply styling to.
    style : dict or DotDict, optional
        Style configuration. If None, uses default FIGRECIPE_STYLE.

    Returns
    -------
    float
        Trace line width in points.

    Examples
    --------
    >>> import figrecipe as ps
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> trace_lw = ps.apply_style(ax)
    >>> ax.plot(x, y, lw=trace_lw)
    """
    import matplotlib.axes

    # Fail loud at the boundary: a non-Axes first positional (commonly a preset
    # name passed as `apply_style("SCITEX_STYLE")`) otherwise crashes deep
    # inside with an opaque `'str' object has no attribute ...` (#160).
    if not isinstance(ax, matplotlib.axes.Axes):
        raise TypeError(
            f"apply_style(ax, style=...): ax must be a matplotlib Axes, "
            f"got {type(ax).__name__}. If you meant a style preset, pass it "
            f"as the style argument: apply_style(ax, style=...)."
        )

    from ..styles._internal import apply_style_mm, get_style, to_subplots_kwargs

    if style is None:
        style = to_subplots_kwargs(get_style())
    elif hasattr(style, "to_subplots_kwargs"):
        style = style.to_subplots_kwargs()
    return apply_style_mm(ax, style)


class _StyleProxy:
    """Proxy object for lazy style loading."""

    def __getattr__(self, name):
        from ..styles._style_loader import STYLE

        return getattr(STYLE, name)

    def to_subplots_kwargs(self):
        from ..styles._internal import to_subplots_kwargs

        return to_subplots_kwargs()


# Create style proxy
STYLE = _StyleProxy()
