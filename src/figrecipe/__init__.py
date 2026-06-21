#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Module docstring is defined below (static default; rebranded lazily).

from __future__ import annotations

# =============================================================================
# IMPORT-TIME BUDGET (audit-cli §10): a bare ``import figrecipe`` must stay
# well under the marginal threshold so Click tab-completion (which re-runs the
# program once per Tab press) stays snappy.
#
# Therefore the module body does the BARE MINIMUM: resolve __version__, install
# the cheap pure-stdlib _compat sys.modules aliases (the back-compat tests do
# ``import figrecipe`` then ``import figrecipe._validator`` with no attribute
# access, so the aliases must exist eagerly), and declare the lazy maps.
#
# Everything with any real cost — the scitex_config .env walk (a filesystem
# walk that can spike on a loaded/NFS CI node), the branding/docstring rebrand,
# the brand-triggered house-style hook, matplotlib, and every public symbol —
# is deferred to first attribute access via PEP 562 ``__getattr__``.
# =============================================================================

# --- Version (must stay eager: cheap, and consumers read it without touching
# any heavy attribute) -------------------------------------------------------
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_version

    try:
        __version__ = _get_version("figrecipe")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _get_version, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"


# --- Back-compat module aliases (#141 _quality topical refactor) -------------
# install_module_aliases() only registers lazy proxy entries in sys.modules
# (pure stdlib, no heavy import); the real modules load on first access. It
# must run eagerly so ``import figrecipe; import figrecipe._validator`` works
# even with no attribute access in between (see tests/figrecipe/_compat/).
from ._compat import install_module_aliases as _install_module_aliases

_install_module_aliases()
del _install_module_aliases


# --- Static module docstring (default brand) --------------------------------
# Non-default brands (parent packages such as scitex.plt) rebrand this lazily
# in _bootstrap() on first attribute access — keeping `import figrecipe` from
# paying the branding import up-front.
__doc__ = """
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

Notes
-----
Submodules:

- ``fr.utils``: Unit conversions, font checks, low-level recipe access
- ``fr.styles``: Axis helpers, spine management, plot styling functions
- ``fr.viz``: Diagram and graph visualization utilities

>>> from figrecipe import utils
>>> utils.mm_to_inch(25.4)  # Unit conversions

>>> from figrecipe import styles
>>> styles.hide_spines(ax)  # Spine management
"""


# =============================================================================
# CORE PUBLIC API - lazy via PEP 562 __getattr__ (audit-cli §10).
#
# Click runs the program once per Tab press for shell completion, so a slow
# top-level import (mostly matplotlib + the diagram subsystem) makes
# tab-completion noticeably sluggish. The map below records (submodule,
# attribute) for every public name; each entry imports lazily on first use.
# =============================================================================
_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    # ._api._public
    "crop": ("._api._public", "crop"),
    "extract_data": ("._api._public", "extract_data"),
    "gui": ("._api._public", "gui"),
    "info": ("._api._public", "info"),
    "load": ("._api._public", "load"),
    "reproduce": ("._api._public", "reproduce"),
    "save": ("._api._public", "save"),
    "subplots": ("._api._public", "subplots"),
    "validate": ("._api._public", "validate"),
    "validate_recipe": ("._api._public", "validate_recipe"),
    # ._api._signature
    "caption_with_signature": ("._api._signature", "caption_with_signature"),
    "signature": ("._api._signature", "signature"),
    # ._api._style_manager
    "list_presets": ("._api._style_manager", "list_presets"),
    "load_style": ("._api._style_manager", "load_style"),
    "unload_style": ("._api._style_manager", "unload_style"),
    # ._bundle
    "Figz": ("._bundle", "Figz"),
    "Pltz": ("._bundle", "Pltz"),
    "save_bundle": ("._bundle", "save_bundle"),
    "load_bundle": ("._bundle", "load_bundle"),
    "reproduce_bundle": ("._bundle", "reproduce_bundle"),
    # ._captions (public caption API)
    "add_figure_caption": ("._captions._public", "add_figure_caption"),
    "add_panel_captions": ("._captions._public", "add_panel_captions"),
    # ._composition
    "align_panels": ("._composition", "align_panels"),
    "align_smart": ("._composition", "align_smart"),
    "compose": ("._composition", "compose"),
    "distribute_panels": ("._composition", "distribute_panels"),
    # ._configure_mpl
    "configure_mpl": ("._configure_mpl", "configure_mpl"),
    # ._diagram
    "Diagram": ("._diagram", "Diagram"),
    "_Graphviz": ("._diagram._graphviz.graphviz", "Graphviz"),
    "_Mermaid": ("._diagram._mermaid.mermaid", "Mermaid"),
    # ._graph._presets
    "get_graph_preset": ("._graph._presets", "get_preset"),
    "list_graph_presets": ("._graph._presets", "list_presets"),
    "register_graph_preset": ("._graph._presets", "register_preset"),
    # ._graph (draw)
    "draw_graph": ("._graph", "draw_graph"),
    # ._spec_builders
    "build_spec": ("._spec_builders", "build_spec"),
    "build_spec_from_csv": ("._spec_builders", "build_spec_from_csv"),
    "XY_KINDS": ("._spec_builders", "XY_KINDS"),
    "DATA_KINDS": ("._spec_builders", "DATA_KINDS"),
    "LABEL_KINDS": ("._spec_builders", "LABEL_KINDS"),
    "MATRIX_KINDS": ("._spec_builders", "MATRIX_KINDS"),
    "ALL_KINDS": ("._spec_builders", "ALL_KINDS"),
    "KIND_ALIASES": ("._spec_builders", "KIND_ALIASES"),
    # ._render
    "render_spec_to_bytes": ("._render", "render_spec_to_bytes"),
    # ._utils._nice_lim  (issue #140)
    "nice_lim": ("._utils._nice_lim", "nice_lim"),
    # ._utils._termplot
    "termplot": ("._utils._termplot", "termplot"),
    # ._api._style_manager (style helpers)
    "STYLE": ("._api._style_manager", "STYLE"),
    "apply_style": ("._api._style_manager", "apply_style"),
    # .presets (flat SCITEX_STYLE preset — subplots() kwargs)
    "SCITEX_STYLE": (".presets._scitex_style", "SCITEX_STYLE"),
    # ._api._notebook
    "enable_svg": ("._api._notebook", "enable_svg"),
    # ._api._public (editor alias)
    "edit": ("._api._public", "gui"),
    # ._editable
    "export_editable": ("._editable", "export_editable"),
    # ._wrappers
    "panel_label": ("._wrappers._panel_labels", "panel_label"),
    # ._composition (alias)
    "smart_align": ("._composition", "align_smart"),
    # ._qr (figure-level QR overlay; pure-stdlib top, matplotlib lazy in-body)
    "add_qr_to_figure": ("._qr", "add_qr_to_figure"),
}


# Module-level so PA-102's PEP-562 detector sees these names as bound
# (it pulls keys from any module-level dict subscripted with `name` inside
# __getattr__). Maps public submodule names → relative import paths.
_MODULE_ALIASES: dict[str, str] = {
    "colors": ".colors",
    "color": ".colors",
    "styles": ".styles",
    "presets": ".presets",
    "utils": ".utils",
    "gallery": "._dev.demo_plotters",
}


# Guard so the one-time bootstrap (env load + branding) runs at most once,
# on the first attribute access — never during a bare ``import figrecipe``.
_BOOTSTRAPPED = False


def _bootstrap() -> None:
    """One-time, lazy initialization deferred out of the import hot path.

    Runs on the first attribute access (from ``__getattr__``), i.e. before any
    figrecipe function executes but after ``import figrecipe`` returns. Does:

    1. Best-effort ``.env`` loading (walk parent dirs from cwd up to $HOME,
       closest wins). This is a filesystem walk — keeping it out of the import
       body is what stops a loaded/NFS CI node from spiking the §10 budget.
    2. Brand-triggered house style: when a parent package (e.g. scitex.plt)
       sets ``FIGRECIPE_BRAND``, apply that brand's global plotting style and
       rebrand this module's ``__doc__``. No-op for the default brand.

    All steps are wrapped tolerantly so a missing/broken scitex-config or
    branding module never breaks attribute resolution.
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    _BOOTSTRAPPED = True

    # 1. .env loading (best-effort, tolerant).
    try:
        from pathlib import Path as _Path

        from scitex_config import load_dotenv as _load_dotenv

        _load_dotenv(walk_up=True, stop_at=str(_Path.home()))
    except Exception:
        pass

    # 2. Branding / house-style (only meaningful for a non-default brand).
    try:
        from ._branding import BRAND_NAME as _BRAND_NAME
        from ._branding import rebrand_text as _rebrand_text

        if _BRAND_NAME != "figrecipe":
            globals()["__doc__"] = _rebrand_text(__doc__)
            try:
                from ._brand_style import apply_brand_style as _apply_brand_style

                _apply_brand_style(_BRAND_NAME)
            except Exception:
                pass
    except Exception:
        pass


def __getattr__(name: str):
    """PEP 562 lazy attribute resolution for the figrecipe public surface."""
    # First touch of any public attribute triggers the deferred bootstrap
    # (env + branding); kept out of the import body for the §10 budget.
    if not _BOOTSTRAPPED:
        _bootstrap()
    if name in _LAZY_ATTRS:
        import importlib

        # Patch on first matplotlib-touching access — see _patch_pyplot_close.
        _patch_pyplot_close()
        module_path, attr = _LAZY_ATTRS[name]
        module = importlib.import_module(module_path, __name__)
        value = getattr(module, attr)
        globals()[name] = value  # cache subsequent accesses
        return value
    if name in _MODULE_ALIASES:
        import importlib

        value = importlib.import_module(_MODULE_ALIASES[name], __name__)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Expose lazy names for tab completion in REPLs."""
    return sorted(set(__all__) | set(_LAZY_ATTRS.keys()) | set(_MODULE_ALIASES.keys()))


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
    "add_qr_to_figure",
    # Caption API
    "add_figure_caption",
    "add_panel_captions",
    "panel_label",
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
    "color",
    # Submodules surfaced as figrecipe attributes
    "styles",
    "presets",
    "utils",
    "gallery",
    # Spec builders / kind registries
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
    # Graph / style / editor helpers
    "draw_graph",
    "smart_align",
    "edit",
    "export_editable",
    "enable_svg",
    "STYLE",
    "SCITEX_STYLE",
    "apply_style",
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
    inheritance) with a TypeError. We wrap ``plt.close`` once so that passing
    a ``RecordingFigure`` transparently unwraps to the underlying
    ``matplotlib.figure.Figure``.

    Called lazily from ``__getattr__`` on first access of any matplotlib-
    touching attribute, so importing figrecipe does not pay the matplotlib.pyplot
    import cost up-front (audit-cli §10).
    """
    import sys

    # If matplotlib.pyplot was never imported, defer further: triggering it
    # here would defeat the lazy-import goal. The next attribute access in
    # __getattr__ that resolves through ._api._public will already pull it in,
    # at which point this patch is idempotent.
    _plt = sys.modules.get("matplotlib.pyplot")
    if _plt is None:
        return
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
