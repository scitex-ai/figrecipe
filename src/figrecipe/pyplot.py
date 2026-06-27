#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drop-in replacement for matplotlib.pyplot with recording capabilities.

This module provides a convenient way to use figrecipe as a direct replacement
for matplotlib.pyplot. Simply change your import statement:

    # Before (standard matplotlib)
    import matplotlib.pyplot as plt

    # After (figrecipe with recording)
    import figrecipe.pyplot as plt

All your existing code will work unchanged, but figures created with
plt.subplots() will automatically have recording capabilities.

Examples
--------
>>> import figrecipe.pyplot as plt
>>> import numpy as np
>>>
>>> x = np.linspace(0, 10, 100)
>>> y = np.sin(x)
>>>
>>> fig, ax = plt.subplots()  # Recording-enabled
>>> ax.plot(x, y, color='red', id='sine_wave')
>>> fig.save_recipe('my_figure.yaml')  # Save as recipe
>>>
>>> # All other pyplot functions work as usual
>>> plt.show()
>>> plt.savefig('output.png')
"""

import matplotlib.pyplot as _plt
from matplotlib.pyplot import *  # noqa: F401, F403

from . import save as _ps_save

# Import figrecipe functionality
from . import subplots as _ps_subplots
from ._wrappers import RecordingFigure

# Override subplots with recording-enabled version
subplots = _ps_subplots


def colorbar(mappable=None, cax=None, ax=None, **kwargs):
    """Add a colorbar, recording it when the target figure is recording.

    Drop-in for ``matplotlib.pyplot.colorbar``. A manual colorbar call on a
    figrecipe figure (``plt.colorbar(im, cax=...)`` / ``plt.colorbar(im, ax=...)``)
    must be recorded or it is DROPPED when the figure is rebuilt from its recipe.
    matplotlib's ``plt.colorbar`` only ever sees the RAW current figure, so this
    wrapper resolves the owning ``RecordingFigure`` -- from an explicit ``cax``/
    ``ax`` axes, the mappable's axes, or ``plt.gcf()`` -- and delegates to its
    recording ``.colorbar``. When no recording figure owns the target (plain
    matplotlib usage), it falls back to the raw ``matplotlib.pyplot.colorbar``.

    Parameters mirror ``matplotlib.pyplot.colorbar``.
    """
    from ._wrappers._figure_registry import get_recording_figure

    def _fig_of(obj):
        a = getattr(obj, "_ax", obj)  # unwrap RecordingAxes
        return getattr(a, "figure", None)

    # Resolve the raw figure the colorbar will be drawn on, preferring the most
    # explicit hint, then fall back to the current figure.
    raw_fig = None
    for hint in (cax, ax):
        if hint is not None and not isinstance(hint, (list, tuple)):
            raw_fig = _fig_of(hint)
            if raw_fig is not None:
                break
    if raw_fig is None and isinstance(ax, (list, tuple)) and ax:
        raw_fig = _fig_of(ax[0])
    if raw_fig is None and mappable is not None:
        raw_fig = getattr(getattr(mappable, "axes", None), "figure", None)
    if raw_fig is None:
        raw_fig = _plt.gcf()

    wrapper = get_recording_figure(raw_fig)
    if wrapper is not None:
        # RecordingFigure.colorbar takes ``cax`` via **kwargs.
        if cax is not None:
            kwargs["cax"] = cax
        return wrapper.colorbar(mappable, ax=ax, **kwargs)

    # No recording figure -> behave exactly like matplotlib.
    if cax is not None:
        kwargs["cax"] = cax
    if ax is not None:
        kwargs["ax"] = ax
    return _plt.colorbar(mappable, **kwargs)


def figure(*args, **kwargs):
    """Create a new figure with optional recording support.

    This is a pass-through to matplotlib.pyplot.figure().
    For recording support, use subplots() instead.

    Parameters
    ----------
    *args, **kwargs
        Arguments passed to matplotlib.pyplot.figure().

    Returns
    -------
    matplotlib.figure.Figure
        The created figure.
    """
    return _plt.figure(*args, **kwargs)


def save(fig, path, **kwargs):
    """Save a figure (recipe for RecordingFigure, or standard save).

    Parameters
    ----------
    fig : RecordingFigure or Figure
        Figure to save. If RecordingFigure, saves as recipe.
        Otherwise, saves as image using savefig().
    path : str or Path
        Output path. Use .yaml for recipe format.
    **kwargs
        Additional arguments for save.

    Returns
    -------
    Path or tuple
        Saved path (and ValidationResult if validate=True).
    """
    if isinstance(fig, RecordingFigure):
        return _ps_save(fig, path, **kwargs)
    else:
        fig.savefig(path, **kwargs)
        return path


# Expose commonly used functions explicitly for IDE support
show = _plt.show
savefig = _plt.savefig


def close(fig=None):
    """Close a figure window.

    Parameters
    ----------
    fig : None, int, str, Figure, or RecordingFigure
        The figure to close. See matplotlib.pyplot.close() for details.
        RecordingFigure is automatically unwrapped to the underlying Figure.
    """
    if isinstance(fig, RecordingFigure):
        _plt.close(fig.fig)
    else:
        _plt.close(fig)


clf = _plt.clf
cla = _plt.cla
gcf = _plt.gcf
gca = _plt.gca
subplot = _plt.subplot
tight_layout = _plt.tight_layout
suptitle = _plt.suptitle
xlabel = _plt.xlabel
ylabel = _plt.ylabel
title = _plt.title
legend = _plt.legend
xlim = _plt.xlim
ylim = _plt.ylim
grid = _plt.grid
plot = _plt.plot
scatter = _plt.scatter
bar = _plt.bar
hist = _plt.hist
imshow = _plt.imshow
contour = _plt.contour
contourf = _plt.contourf
axhline = _plt.axhline
axvline = _plt.axvline
text = _plt.text
annotate = _plt.annotate
fill_between = _plt.fill_between
errorbar = _plt.errorbar
boxplot = _plt.boxplot
violinplot = _plt.violinplot
pie = _plt.pie
stem = _plt.stem
step = _plt.step
stackplot = _plt.stackplot
streamplot = _plt.streamplot
quiver = _plt.quiver
barbs = _plt.barbs
hexbin = _plt.hexbin
pcolormesh = _plt.pcolormesh
tripcolor = _plt.tripcolor
tricontour = _plt.tricontour
tricontourf = _plt.tricontourf
spy = _plt.spy
matshow = _plt.matshow
specgram = _plt.specgram
psd = _plt.psd
csd = _plt.csd
cohere = _plt.cohere
magnitude_spectrum = _plt.magnitude_spectrum
angle_spectrum = _plt.angle_spectrum
phase_spectrum = _plt.phase_spectrum
xcorr = _plt.xcorr
acorr = _plt.acorr
semilogy = _plt.semilogy
semilogx = _plt.semilogx
loglog = _plt.loglog
polar = _plt.polar
subplot2grid = _plt.subplot2grid
subplot_mosaic = _plt.subplot_mosaic
subplots_adjust = _plt.subplots_adjust
rc = _plt.rc
rcdefaults = _plt.rcdefaults
rcParams = _plt.rcParams
style = _plt.style
cm = _plt.cm
get_cmap = _plt.get_cmap
colormaps = _plt.colormaps


# =============================================================================
# Extended figrecipe surface (so `from figrecipe.pyplot import *` is a
# superset of matplotlib.pyplot + the figrecipe public API). These are the
# names the scitex.plt umbrella aliases. Heavy submodules are resolved lazily
# via __getattr__ to keep `import figrecipe.pyplot` cheap.
# =============================================================================
_LAZY_FR_ATTRS: dict[str, tuple[str, str]] = {
    # Spec builders / kind registries
    "build_spec": ("._spec_builders", "build_spec"),
    "build_spec_from_csv": ("._spec_builders", "build_spec_from_csv"),
    "XY_KINDS": ("._spec_builders", "XY_KINDS"),
    "DATA_KINDS": ("._spec_builders", "DATA_KINDS"),
    "LABEL_KINDS": ("._spec_builders", "LABEL_KINDS"),
    "MATRIX_KINDS": ("._spec_builders", "MATRIX_KINDS"),
    "ALL_KINDS": ("._spec_builders", "ALL_KINDS"),
    "KIND_ALIASES": ("._spec_builders", "KIND_ALIASES"),
    # Rendering
    "render_spec_to_bytes": ("._render", "render_spec_to_bytes"),
    # Terminal plotting
    "termplot": ("._utils._termplot", "termplot"),
    # Graph / composition / editor / svg
    "draw_graph": ("._graph", "draw_graph"),
    "smart_align": ("._composition", "align_smart"),
    "align_smart": ("._composition", "align_smart"),
    "enable_svg": ("._api._notebook", "enable_svg"),
    "edit": ("._api._public", "gui"),
    "gui": ("._api._public", "gui"),
    # Style management
    "STYLE": ("._api._style_manager", "STYLE"),
    "apply_style": ("._api._style_manager", "apply_style"),
    "load_style": ("._api._style_manager", "load_style"),
    "unload_style": ("._api._style_manager", "unload_style"),
    "list_presets": ("._api._style_manager", "list_presets"),
    # Flat SCITEX_STYLE preset (subplots() kwargs)
    "SCITEX_STYLE": (".presets._scitex_style", "SCITEX_STYLE"),
    # figrecipe top-level public API (so figrecipe.pyplot is a COMPLETE superset
    # of the figrecipe namespace — lets scitex.plt be a pure alias to this module)
    "compose": (".", "compose"),
    "crop": (".", "crop"),
    "Diagram": (".", "Diagram"),
    "align_panels": (".", "align_panels"),
    "distribute_panels": (".", "distribute_panels"),
    "extract_data": (".", "extract_data"),
    "get_graph_preset": (".", "get_graph_preset"),
    "list_graph_presets": (".", "list_graph_presets"),
    "register_graph_preset": (".", "register_graph_preset"),
    "info": (".", "info"),
    "load": (".", "load"),
    "load_bundle": (".", "load_bundle"),
    "save_bundle": (".", "save_bundle"),
    "reproduce": (".", "reproduce"),
    "reproduce_bundle": (".", "reproduce_bundle"),
    "validate": (".", "validate"),
    "sns": (".", "sns"),
}

# Submodules surfaced by name (resolved lazily as modules).
_LAZY_FR_MODULES: dict[str, str] = {
    "color": ".colors",
    "colors": ".colors",
    "styles": ".styles",
    "presets": ".presets",
    "utils": ".utils",
    "gallery": "._dev.demo_plotters",
}


def __getattr__(name):
    """PEP 562 lazy resolution for the extended figrecipe.pyplot surface."""
    import importlib

    if name in _LAZY_FR_ATTRS:
        module_path, attr = _LAZY_FR_ATTRS[name]
        module = importlib.import_module(module_path, __package__)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    if name in _LAZY_FR_MODULES:
        value = importlib.import_module(_LAZY_FR_MODULES[name], __package__)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        set(__all__) | set(_LAZY_FR_ATTRS) | set(_LAZY_FR_MODULES) | set(globals())
    )


__all__ = [
    # Core functions (recording-enabled)
    "subplots",
    "figure",
    "save",
    # Display
    "show",
    "savefig",
    "close",
    "clf",
    "cla",
    # Getters
    "gcf",
    "gca",
    # Layout
    "subplot",
    "subplot2grid",
    "subplot_mosaic",
    "subplots_adjust",
    "tight_layout",
    # Labels and titles
    "suptitle",
    "xlabel",
    "ylabel",
    "title",
    "legend",
    # Limits
    "xlim",
    "ylim",
    # Grid
    "grid",
    # Plot types
    "plot",
    "scatter",
    "bar",
    "hist",
    "imshow",
    "contour",
    "contourf",
    "colorbar",
    "axhline",
    "axvline",
    "text",
    "annotate",
    "fill_between",
    "errorbar",
    "boxplot",
    "violinplot",
    "pie",
    "stem",
    "step",
    "stackplot",
    "streamplot",
    "quiver",
    "barbs",
    "hexbin",
    "pcolormesh",
    "tripcolor",
    "tricontour",
    "tricontourf",
    "spy",
    "matshow",
    "specgram",
    "psd",
    "csd",
    "cohere",
    "magnitude_spectrum",
    "angle_spectrum",
    "phase_spectrum",
    "xcorr",
    "acorr",
    # Log scale
    "semilogy",
    "semilogx",
    "loglog",
    "polar",
    # Configuration
    "rc",
    "rcdefaults",
    "rcParams",
    "style",
    # Colormaps
    "cm",
    "get_cmap",
    "colormaps",
    # Extended figrecipe surface (lazy via __getattr__)
    "build_spec",
    "build_spec_from_csv",
    "XY_KINDS",
    "DATA_KINDS",
    "LABEL_KINDS",
    "MATRIX_KINDS",
    "ALL_KINDS",
    "KIND_ALIASES",
    "render_spec_to_bytes",
    "termplot",
    "draw_graph",
    "smart_align",
    "align_smart",
    "enable_svg",
    "edit",
    "gui",
    "STYLE",
    "SCITEX_STYLE",
    "apply_style",
    "load_style",
    "unload_style",
    "list_presets",
    "color",
    "colors",
    "styles",
    "presets",
    "utils",
    "gallery",
    # figrecipe top-level public API (complete-superset)
    "compose",
    "crop",
    "Diagram",
    "align_panels",
    "distribute_panels",
    "extract_data",
    "get_graph_preset",
    "list_graph_presets",
    "register_graph_preset",
    "info",
    "load",
    "load_bundle",
    "save_bundle",
    "reproduce",
    "reproduce_bundle",
    "validate",
    "sns",
]
