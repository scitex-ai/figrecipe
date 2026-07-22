"""Tests for figrecipe.styles._axis_helpers._spines.

Tick suppression must be REVERSIBLE, and must be checked on the PIXELS.

Doctrine (NullFormatter regression -- a corrupted published figure):
``set_xticklabels([])`` pins a ``NullFormatter`` on the *axis*, so every tick
the author sets AFTERWARDS renders blank -- through any handle, because the
formatter lives on the axis, not on the handle. A heatmap therefore shipped to
human review with its frequency numbers gone.

It survived review because it survived the TESTS: ``get_xticks()`` kept
returning exactly what the author asked for. Only the drawn text was empty. So
every rendering assertion here reads the RENDERED label text -- an object-level
assertion is structurally blind to this class of corruption.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from figrecipe.styles._axis_helpers._spines import hide_spines, show_spines


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
