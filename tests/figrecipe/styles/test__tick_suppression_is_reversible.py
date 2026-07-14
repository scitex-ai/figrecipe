#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tick suppression must be REVERSIBLE, and must be checked on the PIXELS.

``set_xticklabels([])`` pins a ``NullFormatter`` on the *axis*, so every tick the
author sets AFTERWARDS renders blank -- through any handle, because the formatter
lives on the axis, not on the handle. A heatmap therefore shipped to human review
with its frequency numbers gone.

It survived review because it survived the TESTS: ``get_xticks()`` kept returning
exactly what the author asked for. Only the drawn text was empty. So every
assertion here reads the RENDERED label text -- an object-level assertion is
structurally blind to this class of corruption.
"""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe.styles._axis_helpers._spines import (  # noqa: E402
    hide_spines,
    show_spines,
)
from figrecipe.styles._plot_styles import apply_imshow_axes_visibility  # noqa: E402


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
    # Act + Assert
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


# EOF
