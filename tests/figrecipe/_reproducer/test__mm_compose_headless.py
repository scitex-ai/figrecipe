#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: mm-composed reproduction is headless (no pyplot / GUI backend).

The GUI editor reproduces composed recipes in Django worker threads. If the
reproducer builds its figure via ``plt.figure()``, matplotlib tries to load a
GUI figure manager (tkinter) off the main thread and crashes
("partially initialized module 'tkinter'"). The crash is environment-dependent
(only when a GUI backend is the default), so it slips past tests on Agg-default
machines. These guards are portable:

  1. source-level — the module must not import matplotlib.pyplot;
  2. behavioural — the reproduced figure's canvas is the Agg (headless) canvas.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest

import figrecipe as fr
from figrecipe._reproducer import _mm_compose


@pytest.fixture
def composed_recipe(tmp_path):
    """A 2-panel mm-composition saved to a recipe path."""
    r_a = tmp_path / "a.yaml"
    fig_a, ax_a = fr.subplots()
    ax_a.plot([0, 1, 2], [0, 1, 0], id="la")
    fr.save(fig_a, r_a, validate=False, verbose=False)

    r_b = tmp_path / "b.yaml"
    fig_b, ax_b = fr.subplots()
    ax_b.plot([0, 1, 2], [2, 1, 2], id="lb")
    fr.save(fig_b, r_b, validate=False, verbose=False)

    sources = {
        str(r_a): {"xy_mm": (0, 0), "size_mm": (80, 40)},
        str(r_b): {"xy_mm": (0, 42), "size_mm": (80, 40)},
    }
    comp, _ = fr.compose(sources, canvas_size_mm=(82, 84))
    recipe = tmp_path / "composed.yaml"
    fr.save(comp, recipe, validate=False, verbose=False)
    return recipe


class TestMmComposeHeadless:
    def test_module_does_not_import_pyplot(self):
        # Arrange
        source = Path(_mm_compose.__file__).read_text(encoding="utf-8")
        # Act
        uses_pyplot = "matplotlib.pyplot" in source
        # Assert -- pyplot would pull a GUI backend in worker threads
        assert not uses_pyplot

    def test_reproduced_canvas_is_agg(self, composed_recipe):
        # Arrange
        wrapped, _ = fr.reproduce(composed_recipe)
        mpl_fig = wrapped.fig if hasattr(wrapped, "fig") else wrapped
        # Act
        canvas_cls = type(mpl_fig.canvas).__name__
        # Assert -- headless Agg canvas, not a GUI (Tk/Qt) one
        assert "Agg" in canvas_cls

    def test_reproduces_all_panels(self, composed_recipe):
        # Arrange
        wrapped, _ = fr.reproduce(composed_recipe)
        mpl_fig = wrapped.fig if hasattr(wrapped, "fig") else wrapped
        # Act
        n_axes = len(mpl_fig.axes)
        # Assert -- both panels survived (no collapse)
        assert n_axes == 2
