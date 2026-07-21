"""Tests for figrecipe.styles._axis_helpers._spines.

The hide/show round trip must be REVERSIBLE, and must be checked on the
PIXELS: a pinned ``NullFormatter`` keeps ``get_xticks()`` truthful while every
drawn label is blank, so the assertions here read the RENDERED label text.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe.styles._axis_helpers._spines import (  # noqa: E402
    hide_spines,
    show_spines,
)


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


def test_import_styles__axis_helpers__spines_module():
    # Arrange
    module_path = "figrecipe.styles._axis_helpers._spines"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_hidden_spine_labels_come_back_on_show(heatmap):
    # Arrange: hide_spines(labels=True) then show_spines(labels=True) is the
    # documented round trip. It could never work against a pinned NullFormatter,
    # because show_spines restores by re-setting tick LOCATIONS and a formatter
    # outranks those. (hide_spines defaults to bottom=False, so name the axis.)
    heatmap.set_xticks([0, 1])
    hide_spines(heatmap, bottom=True, labels=True)
    # Act
    show_spines(heatmap, top=False, right=False, labels=True)
    # Assert
    assert _drawn_xlabels(heatmap) == ["0", "1"]


def test_hide_spines_actually_hides_the_labels(heatmap):
    # Arrange: the round trip above must not be vacuous -- hiding has to hide,
    # or "restored" would prove nothing.
    heatmap.set_xticks([0, 1])
    # Act
    hide_spines(heatmap, bottom=True, labels=True)
    # Assert
    assert _drawn_xlabels(heatmap) == []
