"""Tests for AxesStyleMixin spine list-arg fix.

Per neurovista 2026-06-14: ``hide_spines`` / ``show_spines`` /
``toggle_spines`` on the mixin previously forwarded the list as the
first positional argument to the low-level helper (which expects
per-side booleans), so ``ax.hide_spines(['top','right','left','bottom'])``
only hid top + right regardless of the list contents.

These tests construct a plain matplotlib axes, drive the mixin against
it, and assert spine visibility on every side.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe._wrappers._axes_style_mixin import AxesStyleMixin  # noqa: E402

# NOTE: rcParams isolation is provided process-wide by the autouse
# ``_isolate_matplotlib_rcparams`` fixture in ``tests/conftest.py`` (it
# snapshots ``matplotlib.rcParams`` before each test and restores them after),
# so these tests see a fresh axes with matplotlib's stock spine defaults
# regardless of test order / xdist worker. A module-local rcParams reset is no
# longer needed.


class _StubAxesWrapper(AxesStyleMixin):
    """Minimal wrapper that exposes a real matplotlib axis as ``self._ax``.

    The mixin only touches ``self._ax`` for spine ops, so we don't need
    the full RecordingAxes machinery here.
    """

    def __init__(self, ax):
        self._ax = ax


def _make_ax():
    fig, ax = plt.subplots()
    return _StubAxesWrapper(ax), ax, fig


# ---------------------------------------------------------------------------
# hide_spines
# ---------------------------------------------------------------------------


def test_hide_spines_with_full_list_hides_all_four_sides():
    # Arrange
    wrapper, ax, fig = _make_ax()

    # Act
    wrapper.hide_spines(["top", "right", "left", "bottom"])

    # Assert
    hidden = {
        s: not ax.spines[s].get_visible() for s in ("top", "bottom", "left", "right")
    }
    plt.close(fig)
    assert hidden == {"top": True, "bottom": True, "left": True, "right": True}


def test_hide_spines_default_hides_top_and_right_only():
    # Arrange
    wrapper, ax, fig = _make_ax()

    # Act
    wrapper.hide_spines()

    # Assert
    visible = {
        s: ax.spines[s].get_visible() for s in ("top", "bottom", "left", "right")
    }
    plt.close(fig)
    assert visible == {"top": False, "bottom": True, "left": True, "right": False}


def test_hide_spines_list_hides_exactly_requested_sides():
    # Arrange
    wrapper, ax, fig = _make_ax()

    # Act — request only left and bottom.
    wrapper.hide_spines(["left", "bottom"])

    # Assert — only left + bottom hidden; top + right stay visible (per the
    # "exactly these" semantics; top/right defaults are overridden when a
    # list is given).
    visible = {
        s: ax.spines[s].get_visible() for s in ("top", "bottom", "left", "right")
    }
    plt.close(fig)
    assert visible == {"top": True, "bottom": False, "left": False, "right": True}


# ---------------------------------------------------------------------------
# show_spines
# ---------------------------------------------------------------------------


def test_show_spines_with_classic_pair_shows_only_left_and_bottom():
    # Arrange — start with all four spines hidden so we can see only the
    # ones we ask show_spines to display.
    wrapper, ax, fig = _make_ax()
    for s in ("top", "bottom", "left", "right"):
        ax.spines[s].set_visible(False)

    # Act
    wrapper.show_spines(["left", "bottom"])

    # Assert
    visible = {
        s: ax.spines[s].get_visible() for s in ("top", "bottom", "left", "right")
    }
    plt.close(fig)
    assert visible == {"top": False, "bottom": True, "left": True, "right": False}


# ---------------------------------------------------------------------------
# toggle_spines
# ---------------------------------------------------------------------------


def test_toggle_spines_toggles_only_listed_sides():
    # Arrange — all four start visible (matplotlib default).
    wrapper, ax, fig = _make_ax()

    # Act — toggle top + bottom only.
    wrapper.toggle_spines(["top", "bottom"])

    # Assert — top + bottom flipped to hidden; left + right unchanged.
    visible = {
        s: ax.spines[s].get_visible() for s in ("top", "bottom", "left", "right")
    }
    plt.close(fig)
    assert visible == {"top": False, "bottom": False, "left": True, "right": True}


# EOF
