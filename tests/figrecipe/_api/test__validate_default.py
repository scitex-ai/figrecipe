"""Regression test for the default value of ``validate_error_level``.

Pinned to ``"warning"`` so a successful save followed by an
informational reproducibility check never aborts the user's
script — the PNG is already on disk by the time the validator
runs, and common matplotlib primitives that aren't yet captured
by the recipe (axhspan, fill_between, symlog, set_xticks with
arrays, etc.) routinely produce pixel-MSE above the default 100
threshold even when the saved image is visually correct.

If you change the default, also update issue #134 and the docstrings
in ``_api/_public.py::save`` and ``_api/_save.py::save_figure``.
"""

from __future__ import annotations

import inspect

import pytest


def _default_for(fn, param_name):
    sig = inspect.signature(fn)
    return sig.parameters[param_name].default


def test_public_save_default_validate_error_level_is_warning():
    fr = pytest.importorskip("figrecipe")
    default = _default_for(fr.save, "validate_error_level")
    assert default == "warning", (
        "figrecipe.save default `validate_error_level` should be "
        f"'warning', got {default!r}. See issue #134 for the rationale: "
        "validation runs after the PNG is already on disk, so a hard "
        "raise on common-matplotlib MSE blow-ups aborts the user "
        "script after a successful save."
    )


def test_internal_save_figure_default_validate_error_level_is_warning():
    save_mod = pytest.importorskip("figrecipe._api._save")
    default = _default_for(save_mod.save_figure, "validate_error_level")
    assert default == "warning", (
        "figrecipe._api._save.save_figure default `validate_error_level` "
        f"should be 'warning', got {default!r}. This default is the "
        "single source of truth for the public-API default in "
        "figrecipe.save."
    )


def test_public_save_default_validate_error_level_matches_internal():
    """The public `save` wrapper must mirror the internal `save_figure` default.

    Drift here breaks the validation-policy invariant the docs promise.
    """
    fr = pytest.importorskip("figrecipe")
    save_mod = pytest.importorskip("figrecipe._api._save")
    pub = _default_for(fr.save, "validate_error_level")
    internal = _default_for(save_mod.save_figure, "validate_error_level")
    assert pub == internal, (
        f"figrecipe.save (default {pub!r}) and "
        f"figrecipe._api._save.save_figure (default {internal!r}) "
        "must agree on validate_error_level. Update both together."
    )


def test_save_recipe_false_returns_without_validation():
    """Ask (3): ``save_recipe=False`` must short-circuit before validation.

    Inspect the source rather than rendering — the regression check is
    purely structural so it never depends on matplotlib state.
    """

    save_mod = pytest.importorskip("figrecipe._api._save")
    src = inspect.getsource(save_mod.save_figure)
    # The function must contain a guard that returns BEFORE the
    # validation block when save_recipe is False. We look for the
    # ``if not save_recipe`` block followed by a ``return`` within a
    # window of a few lines.
    lines = src.splitlines()
    found = False
    for i, line in enumerate(lines):
        if "if not save_recipe" in line:
            window = " ".join(lines[i : i + 6])
            if "return" in window:
                found = True
                break
    assert found, (
        "save_figure must early-return when save_recipe=False, before "
        "any validation runs. See issue #134 ask (3)."
    )
