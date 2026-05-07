#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Module docstring is defined below after branding import

# Branding support (must be imported first, before docstring is set)
from __future__ import annotations

from ._branding import rebrand_text as _rebrand_text

# Define module docstring with branding applied
_RAW_DOC = """
figrecipe - Record and reproduce matplotlib figures.

A lightweight library for capturing matplotlib plotting calls and
reproducing figures from saved recipes.

Usage
-----
>>> import figrecipe as fr
>>> fig, ax = fr.subplots()
>>> ax.plot(x, y, id='my_data')
>>> fr.save(fig, 'recipe.yaml')

Examples
--------
Recording a figure:

>>> import figrecipe as fr
>>> import numpy as np
>>>
>>> x = np.linspace(0, 10, 100)
>>> y = np.sin(x)
>>>
>>> fig, ax = fr.subplots()
>>> ax.plot(x, y, color='red', linewidth=2, id='sine_wave')
>>> ax.set_xlabel('Time')
>>> ax.set_ylabel('Amplitude')
>>> fr.save(fig, 'my_figure.yaml')

Reproducing a figure:

>>> fig, ax = fr.reproduce('my_figure.yaml')
>>> plt.show()

Submodules
----------
- fr.utils: Unit conversions, font checks, low-level recipe access
- fr.styles: Axis helpers, spine management, plot styling functions
- fr.viz: Diagram and graph visualization utilities

>>> from figrecipe import utils
>>> utils.mm_to_inch(25.4)  # Unit conversions

>>> from figrecipe import styles
>>> styles.hide_spines(ax)  # Spine management
"""
__doc__ = _rebrand_text(_RAW_DOC)

# Version
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_version

    try:
        __version__ = _get_version("figrecipe")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"

# =============================================================================
# CORE PUBLIC API - Minimal, essential functions only
# =============================================================================
from . import colors
from ._api._public import (
    crop,
    extract_data,
    gui,
    info,
    load,
    reproduce,
    save,
    subplots,
    validate,
    validate_recipe,  # backward compat alias
)
from ._api._signature import caption_with_signature, signature
from ._api._style_manager import list_presets, load_style, unload_style
from ._bundle import Figz, Pltz, load_bundle, reproduce_bundle, save_bundle
from ._composition import align_panels, align_smart, compose, distribute_panels
from ._configure_mpl import configure_mpl  # noqa: F401
from ._diagram import Diagram
from ._diagram._graphviz.graphviz import Graphviz as _Graphviz  # noqa: F401
from ._diagram._mermaid.mermaid import Mermaid as _Mermaid  # noqa: F401

# Graph preset functions: accessible but not in __all__ (keep for scitex.plt compat)
from ._graph._presets import get_preset as get_graph_preset  # noqa: F401
from ._graph._presets import list_presets as list_graph_presets  # noqa: F401
from ._graph._presets import register_preset as register_graph_preset  # noqa: F401


# Lazy seaborn access (avoids import error if seaborn not installed)
class _SnsModule:
    def __getattr__(self, name):
        from ._seaborn import get_seaborn_recorder

        return getattr(get_seaborn_recorder(), name)


sns = _SnsModule()

# =============================================================================
# PUBLIC API (__all__ controls tab-completion - keep minimal)
# =============================================================================

__all__ = [
    # Core workflow
    "subplots",
    "save",
    "reproduce",
    "load",
    "compose",
    "align_panels",
    "distribute_panels",
    "align_smart",
    "gui",
    "crop",
    "info",
    "validate",
    "extract_data",
    # Bundle format
    "Figz",
    "Pltz",
    "save_bundle",
    "load_bundle",
    "reproduce_bundle",
    # Style management
    "load_style",
    "unload_style",
    "list_presets",
    # Diagram
    "Diagram",
    # Color utilities
    "colors",
    # Signature
    "signature",
    "caption_with_signature",
    # Seaborn integration
    "sns",
    # Version
    "__version__",
]


def _patch_pyplot_close() -> None:
    """Make ``matplotlib.pyplot.close`` accept ``RecordingFigure`` instances.

    ``plt.close()`` uses ``isinstance(fig, Figure)`` as its type check, which
    rejects figrecipe's ``RecordingFigure`` wrapper (composition, not
    inheritance) with a TypeError. We wrap ``plt.close`` once at import time
    so that passing a ``RecordingFigure`` transparently unwraps to the
    underlying ``matplotlib.figure.Figure``.
    """
    import matplotlib.pyplot as _plt

    if getattr(_plt.close, "_figrecipe_patched", False):
        return

    _orig_close = _plt.close

    def close(fig=None):
        from ._wrappers._figure import RecordingFigure

        if isinstance(fig, RecordingFigure):
            fig = fig._fig
        return _orig_close(fig)

    close._figrecipe_patched = True  # type: ignore[attr-defined]
    close.__wrapped__ = _orig_close  # type: ignore[attr-defined]
    close.__doc__ = _orig_close.__doc__
    _plt.close = close


_patch_pyplot_close()
