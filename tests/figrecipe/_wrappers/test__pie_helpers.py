#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pie chrome suppression must be REVERSIBLE, and checked on the PIXELS.

``apply_pie_axes_visibility`` is the pie twin of the imshow suppressor, and it
kept the defect two releases longer: ``set_xticklabels([])`` pins a
``NullFormatter`` on the *axis*, so every tick the author sets afterwards
renders blank through any handle, with no way to undo it.

The assertions read RENDERED text. ``get_xticks()`` reports the author's own
values back to them while the picture is empty, which is exactly how a blank
heatmap once passed both review and a green test suite.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe._wrappers._pie_helpers import (  # noqa: E402
    apply_pie_axes_visibility,
)

_SUPPRESS = {"show_axes": False}


def _drawn_xlabels(ax):
    """The tick label text actually RENDERED -- not what get_xticks() claims."""
    ax.figure.canvas.draw()
    return [t.get_text() for t in ax.get_xticklabels() if t.get_visible()]


@pytest.fixture
def pie_ax():
    fig, ax = plt.subplots()
    ax.pie([1, 2, 3])
    yield ax
    plt.close(fig)


def test_author_ticks_render_after_pie_suppression(pie_ax):
    # Arrange: styling hides the chrome, then the author pins real ticks -- the
    # order that blanked a comodulogram everywhere else this pattern appeared.
    apply_pie_axes_visibility(pie_ax, _SUPPRESS)
    # Act
    pie_ax.set_xticks([0, 1])
    # Assert: the NUMBERS are on the page, not merely in get_xticks().
    assert _drawn_xlabels(pie_ax) == ["0", "1"]


def test_pie_suppression_leaves_no_null_formatter(pie_ax):
    # Arrange: a pinned NullFormatter is the mechanism -- nothing can undo it.
    from matplotlib.ticker import NullFormatter

    # Act
    apply_pie_axes_visibility(pie_ax, _SUPPRESS)
    # Assert
    assert not isinstance(pie_ax.xaxis.get_major_formatter(), NullFormatter)
    assert not isinstance(pie_ax.yaxis.get_major_formatter(), NullFormatter)


def test_pie_suppression_actually_hides_the_chrome(pie_ax):
    # Arrange: the reversibility test above must not be vacuous -- suppression
    # still has to suppress, or "restored" would prove nothing.
    # Act
    apply_pie_axes_visibility(pie_ax, _SUPPRESS)
    # Assert
    assert _drawn_xlabels(pie_ax) == []
    assert not any(s.get_visible() for s in pie_ax.spines.values())


def test_pie_chrome_is_kept_when_show_axes(pie_ax):
    # Arrange: the flag must still mean something in the other direction.
    # Act
    apply_pie_axes_visibility(pie_ax, {"show_axes": True})
    # Assert
    assert any(s.get_visible() for s in pie_ax.spines.values())


# EOF
