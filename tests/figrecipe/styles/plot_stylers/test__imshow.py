"""Tests for figrecipe.styles.plot_stylers._imshow (incl. aspect honoring)."""

import glob

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest


def test_import_styles_plot_stylers__imshow_module():
    # Arrange
    module_path = "figrecipe.styles.plot_stylers._imshow"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _reproduced_imshow_aspect(tmp_path, aspect_kwarg):
    """Save a SCITEX imshow then reproduce it; return the reproduced aspect.

    ``aspect_kwarg`` is a dict of kwargs forwarded to ``ax.imshow`` so callers
    can include or omit ``aspect``. The aspect is read off the REPRODUCED axes
    so the save->reproduce cycle is exercised (the bug was save-time).
    """
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=40)
    ax.imshow(np.random.rand(28, 120), **aspect_kwarg)
    fr.save(fig, str(tmp_path / "fig.png"))
    yaml_path = glob.glob(str(tmp_path / "*.yaml"))[0]
    reproduced = fr.reproduce(yaml_path)
    rfig = reproduced[0] if isinstance(reproduced, tuple) else reproduced
    mpl_fig = rfig.fig if hasattr(rfig, "fig") else rfig
    return mpl_fig.get_axes()[0].get_aspect()


def test_explicit_imshow_aspect_auto_survives_save_reproduce(tmp_path):
    # Arrange
    aspect_kwarg = {"aspect": "auto"}
    # Act
    reproduced_aspect = _reproduced_imshow_aspect(tmp_path, aspect_kwarg)
    # Assert
    assert reproduced_aspect == "auto"


def test_default_imshow_aspect_stays_equal_when_unspecified(tmp_path):
    # Arrange
    aspect_kwarg = {}
    # Act
    reproduced_aspect = _reproduced_imshow_aspect(tmp_path, aspect_kwarg)
    # Assert
    assert reproduced_aspect == 1.0


def test_styler_honors_explicit_aspect_auto():
    # Arrange
    import figrecipe as fr
    from figrecipe.styles.plot_stylers._imshow import ImshowStyler

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots()
    image = ax.imshow(np.random.rand(10, 10))
    styler = ImshowStyler()
    # Act
    styler.apply(image, ax=ax.ax, aspect="auto")
    # Assert
    assert ax.ax.get_aspect() == "auto"
