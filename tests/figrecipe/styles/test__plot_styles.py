"""Tests for figrecipe.styles._plot_styles.

Focus: imshow axis-chrome suppression must stay REVERSIBLE. A heatmap whose x/y
axes carry physical meaning has to be able to keep its tick numbers.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from figrecipe.styles._plot_styles import apply_imshow_axes_visibility


@pytest.fixture(autouse=True)
def close_figures():
    plt.close("all")
    yield
    plt.close("all")


def test_import_styles__plot_styles_module():
    # Arrange
    module_path = "figrecipe.styles._plot_styles"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_suppression_clears_the_tick_labels():
    # Arrange
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]])
    # Act
    apply_imshow_axes_visibility(ax, show_axes=False, show_labels=True)
    fig.canvas.draw()
    # Assert
    assert [tick.get_text() for tick in ax.get_xticklabels()] == []


def test_suppressed_ticks_can_be_restored_afterwards():
    # Arrange: the caller draws a heatmap, then labels the axes it cares about.
    # Suppression must not pin a NullFormatter -- that blanked every tick set
    # afterwards, leaving a time-by-frequency map with no readable numbers and no
    # way to get them back.
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]], extent=[0, 1, 0, 1])
    apply_imshow_axes_visibility(ax, show_axes=False, show_labels=True)
    # Act
    ax.set_xticks([0.0, 0.5, 1.0])
    fig.canvas.draw()
    # Assert
    assert [tick.get_text() for tick in ax.get_xticklabels()] == ["0.0", "0.5", "1.0"]


def test_restored_y_ticks_are_not_blanked_either():
    # Arrange
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]], extent=[0, 1, 0, 1])
    apply_imshow_axes_visibility(ax, show_axes=False, show_labels=True)
    # Act
    ax.set_yticks([0.0, 1.0])
    fig.canvas.draw()
    # Assert: the exact numeric formatting is matplotlib's business ("0" vs "0.0");
    # the contract is that the restored ticks are not BLANKED.
    assert all(tick.get_text() for tick in ax.get_yticklabels())


def test_show_axes_true_leaves_ticks_alone():
    # Arrange
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]])
    # Act
    apply_imshow_axes_visibility(ax, show_axes=True, show_labels=True)
    fig.canvas.draw()
    # Assert
    assert len(ax.get_xticklabels()) > 0


def test_show_labels_false_clears_the_axis_label():
    # Arrange
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]])
    ax.set_xlabel("Time [s]")
    # Act
    apply_imshow_axes_visibility(ax, show_axes=True, show_labels=False)
    # Assert
    assert ax.get_xlabel() == ""
