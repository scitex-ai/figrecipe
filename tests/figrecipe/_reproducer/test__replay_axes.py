"""Tests for figrecipe._reproducer._replay_axes.

Focus: a heatmap whose author deliberately ticked its axes must reproduce WITH
those ticks. The imshow chrome suppression may clear tick locations, but it must
never pin a formatter that blanks the ticks the author set afterwards.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    plt.close("all")
    yield
    plt.close("all")


def test_import_reproducer__replay_axes_module():
    # Arrange
    module_path = "figrecipe._reproducer._replay_axes"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _labelled_heatmap():
    """A time-by-frequency map: axes carry physical meaning, ticks must survive."""
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.imshow(
        [[1, 2, 3], [4, 5, 6]],
        aspect="auto",
        origin="lower",
        extent=[0, 1, 4, 80],
        id="heatmap",
    )
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Frequency [Hz]")
    return fig, ax


def test_explicit_heatmap_ticks_render_in_the_live_figure():
    # Arrange
    fig, ax = _labelled_heatmap()
    # Act
    fig.fig.canvas.draw()
    # Assert
    assert [tick.get_text() for tick in ax.get_xticklabels()] == ["0.0", "0.5", "1.0"]


def test_explicit_heatmap_ticks_survive_save_and_reproduce(tmp_path):
    # Arrange
    import figrecipe as fr

    fig, _ = _labelled_heatmap()
    recipe = tmp_path / "heatmap.yaml"
    fr.save(fig, recipe, validate=False)
    plt.close("all")
    # Act
    fig2, ax2 = fr.reproduce(recipe)
    fig2.fig.canvas.draw()
    # Assert
    assert [tick.get_text() for tick in ax2.get_xticklabels()] == ["0.0", "0.5", "1.0"]
