"""Tests for figrecipe._scitex_compat._scientific.

Real ax.stx_scatter_hist behaviour (no mocks). Each test follows
Arrange / Act / Assert with one assertion. Tests use matplotlib in the
Agg backend so they're headless-safe.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest


def test_import__scitex_compat__scientific_module():
    # Arrange
    module_path = "figrecipe._scitex_compat._scientific"

    # Act
    mod = pytest.importorskip(module_path)

    # Assert
    assert mod.__name__ == module_path


def _make_marginals(**kwargs):
    """Run stx_scatter_hist on a fresh figure and return the marginal axes.

    Marginal axes are the two children created by
    ``mpl_toolkits.axes_grid1.make_axes_locatable``: one above the scatter
    (the x-marginal — labelled on its y-axis with the count/density text)
    and one to the right (the y-marginal — labelled on its x-axis).

    Axis positions on ``append_axes`` results aren't finalised until the
    layout is computed, so we identify the marginals by which side they
    carry the marginal-label on instead of by bbox.
    """
    from figrecipe._scitex_compat._scientific import stx_scatter_hist

    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x = rng.normal(size=100)
    y = rng.normal(size=100)
    stx_scatter_hist(ax, x, y, **kwargs)
    return fig, list(fig.get_axes())


def test_marginal_histogram_auto_labels_top_y_as_count():
    # Arrange — default histogram mode, marginal_label not passed.

    # Act
    fig, all_axes = _make_marginals()
    ylabels = {a.get_ylabel() for a in all_axes}

    # Assert
    assert "Count" in ylabels
    plt.close(fig)


def test_marginal_histogram_auto_labels_right_x_as_count():
    # Arrange — default histogram mode, marginal_label not passed.

    # Act
    fig, all_axes = _make_marginals()
    xlabels = {a.get_xlabel() for a in all_axes}

    # Assert
    assert "Count" in xlabels
    plt.close(fig)


def test_marginal_label_override_replaces_count_default():
    # Arrange — explicit non-empty value must win over the auto default.

    # Act
    fig, all_axes = _make_marginals(marginal_label="Frequency")
    ylabels = {a.get_ylabel() for a in all_axes}

    # Assert
    assert "Frequency" in ylabels
    plt.close(fig)


def test_marginal_label_empty_string_opts_out_of_auto_label():
    # Arrange — empty string is the documented opt-out path.

    # Act
    fig, all_axes = _make_marginals(marginal_label="")
    ylabels = {a.get_ylabel() for a in all_axes}

    # Assert
    assert "Count" not in ylabels
    plt.close(fig)


# EOF
