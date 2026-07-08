"""STX-FM016 raw-matplotlib-bypass AST checker.

Wrapper module re-exporting :func:`_make_raw_mpl_bypass_checker` from
:mod:`figrecipe._quality._linter_checkers`. This module exists so that the
test file ``tests/figrecipe/_quality/test__raw_mpl_bypass_checker.py`` has a
matching ``src/`` mirror (PS-204 §2 — no orphan test files), and so callers
who only need the raw-mpl-bypass checker do not have to import the larger
``_linter_checkers`` module that also hosts the style-kwarg and figure-method
factories.

``STX-FM016`` flags raw matplotlib figure creation (``plt.subplots`` /
``plt.figure`` / ``matplotlib.pyplot.*`` / bare ``subplots`` imported ``from
matplotlib.pyplot``) that bypasses figrecipe recording — recommend
``fr.subplots`` / ``stx.plt.subplots``.

The factory itself lives in ``_linter_checkers`` (single source of truth,
shared private helpers); splitting it into a real module would force a
circular re-import through ``_linter_plugin``. The shim pattern keeps the
checker importable from a name matching the rule family.
"""

from __future__ import annotations

from figrecipe._quality._linter_checkers import _make_raw_mpl_bypass_checker

__all__ = ["_make_raw_mpl_bypass_checker"]


# EOF
