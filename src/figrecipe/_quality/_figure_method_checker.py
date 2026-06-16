"""STX-FM010 / STX-FM011 figure-method AST checker.

Wrapper module re-exporting :func:`_make_figure_method_checker` from
:mod:`figrecipe._quality._linter_checkers`. This module exists so that
the test file ``tests/figrecipe/_quality/test__figure_method_checker.py``
has a matching ``src/`` mirror (PS-204 §2 — no orphan test files), and
so that callers who only need the figure-method checker do not have to
import the larger ``_linter_checkers`` module that also contains the
style-kwarg checker factory.

Two rules are emitted:

- ``STX-FM010`` flags ``ax.set_xlabel`` / ``ax.set_ylabel`` /
  ``ax.set_title`` calls (recommend ``ax.set_xyt`` instead).
- ``STX-FM011`` flags ``ax.spines[...].set_visible(False)`` (recommend
  ``ax.hide_spines`` instead).

The factory itself lives in ``_linter_checkers`` because the same module
also hosts the style-kwarg checker factory and the two share private
helpers; splitting the figure-method factory into its own real module
would force a circular re-import through ``_linter_plugin``. The shim
pattern keeps both rules importable from a name that matches the rule
family while preserving a single source of truth.
"""

from __future__ import annotations

from figrecipe._quality._linter_checkers import _make_figure_method_checker

__all__ = ["_make_figure_method_checker"]


# EOF
