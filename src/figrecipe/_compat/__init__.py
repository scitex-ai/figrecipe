"""figrecipe._compat — module-rename back-compatibility layer.

The #141 topical refactor moved four private modules into
``figrecipe._quality.``::

    figrecipe._validator                → figrecipe._quality._validator
    figrecipe._linter_plugin            → figrecipe._quality._linter_plugin
    figrecipe._axis_alignment_checker   → figrecipe._quality._axis_alignment_checker
    figrecipe._axis_range_alignment     → figrecipe._quality._axis_range_alignment

The YAGNI grep at lead-gate time showed zero external runtime consumers, so
the move itself didn't break the ecosystem. But the operator asked for
ecosystem-uniform deprecation messaging — when *anything* imports the old
path, the resulting error/warning should be in the canonical scitex-compat
style, not a bare ``ModuleNotFoundError``. That's what this subpackage
provides.

Implementation: ``install_module_aliases()`` registers ``sys.modules``
entries at the old paths so the old imports succeed AND emit a
``DeprecationWarning`` (single-fire per old path) pointing at the new path.
No flat shim files at the package root — keeps the PS-108b flat-file
threshold intact.

This module is imported eagerly from ``figrecipe.__init__`` so the aliases
are live before any consumer touches the old paths.
"""

from ._module_aliases import install_module_aliases

__all__ = ["install_module_aliases"]
