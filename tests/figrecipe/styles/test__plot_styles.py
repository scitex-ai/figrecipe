"""Tests for figrecipe.styles._plot_styles.

Focus: imshow axis-chrome suppression must stay REVERSIBLE. A heatmap whose x/y
axes carry physical meaning has to be able to keep its tick numbers.
"""

import warnings

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


# --- Reversibility checked on the PIXELS, not the objects ---------------------
#
# ``set_xticklabels([])`` pins a ``NullFormatter`` on the *axis*, so every tick
# the author sets AFTERWARDS renders blank -- through any handle, because the
# formatter lives on the axis, not on the handle. A heatmap therefore shipped to
# human review with its frequency numbers gone. It survived review because it
# survived the TESTS: ``get_xticks()`` kept returning exactly what the author
# asked for; only the drawn text was empty. So the assertions below read the
# RENDERED label text -- an object-level assertion is structurally blind to this
# class of corruption.


def _drawn_xlabels(ax):
    """The tick label text actually RENDERED -- not what get_xticks() claims."""
    ax.figure.canvas.draw()
    return [t.get_text() for t in ax.get_xticklabels() if t.get_visible()]


@pytest.fixture
def heatmap():
    fig, ax = plt.subplots()
    ax.imshow([[1, 2], [3, 4]])
    yield ax
    plt.close(fig)


def test_author_ticks_render_after_imshow_suppression(heatmap):
    # Arrange: the styler hides the chrome, then the author pins real ticks --
    # the exact order that produced a blank-axis comodulogram.
    apply_imshow_axes_visibility(heatmap, show_axes=False, show_labels=False)
    # Act
    heatmap.set_xticks([0, 1])
    # Assert: the NUMBERS are on the page, not merely in get_xticks().
    assert _drawn_xlabels(heatmap) == ["0", "1"]


def test_imshow_suppression_leaves_no_null_formatter(heatmap):
    # Arrange: a NullFormatter is the mechanism -- pin it and nothing can undo it.
    from matplotlib.ticker import NullFormatter

    # Act
    apply_imshow_axes_visibility(heatmap, show_axes=False, show_labels=False)
    # Assert
    assert not isinstance(heatmap.xaxis.get_major_formatter(), NullFormatter)


def test_suppressing_explicit_ticks_warns_the_author(heatmap):
    # Arrange: the author explicitly asked for these ticks; the style says hide.
    # Discarding that silently is the defect -- name it.
    heatmap.set_xticks([0, 1])
    # Act
    # Assert
    with pytest.warns(UserWarning, match="tick"):
        apply_imshow_axes_visibility(heatmap, show_axes=False, show_labels=False)


def test_default_ticks_are_suppressed_without_warning(heatmap):
    # Arrange: nothing was author-set, so hiding the chrome discards no choice
    # and must stay quiet -- a warning on every heatmap would be noise.
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        apply_imshow_axes_visibility(heatmap, show_axes=False, show_labels=False)
    # Assert
    assert not [w for w in caught if "tick" in str(w.message)]
