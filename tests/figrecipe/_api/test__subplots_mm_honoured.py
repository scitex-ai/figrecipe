"""The mm promise: an axes asked for in mm must render at that size.

These are EXACT assertions, unlike the relationship-only tests in
tests/figrecipe/_composition/test__compose.py. An exact number is justified here
because _api/_subplots.py states the arithmetic outright -- the figure is sized
as ``margins + ncols*axes_width_mm + gaps`` (lines ~108-112) and the axes region
is positioned to span exactly ``ncols*axes_width_mm + gaps`` (lines ~150-157).
So a single axes requested at 60mm has one correct rendered width: 60mm.

Measured 2026-08-09: it lands exactly, but ONLY when constrained_layout is off.
constrained_layout recomputes axes positions from decoration extents and
overwrites the mm fractions, inflating a 60mm axes to ~82mm. The figure's overall
size stays correct (it came from the same mm numbers), so nothing in the output
looks wrong -- which is what made this invisible.

See figrecipe-rendered-axes-exceeds-requested-mm-by-a-constant-20260809.
"""

from __future__ import annotations

import warnings

import pytest

import figrecipe as fr
from figrecipe._utils._dimension_info import get_dimension_info

_DISCARD_MARKER = "mm layout was computed"


def _axes_size_mm(fig):
    """The rendered axes size, measured after the canvas is drawn."""
    return get_dimension_info(fig.fig, fig.fig.axes[0])["axes_size_mm"]


def _subplots_capturing_warnings(**kwargs):
    """Build a figure and return it with any mm-discarded warnings raised."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, _ = fr.subplots(**kwargs)
    discarded = [w for w in caught if _DISCARD_MARKER in str(w.message)]
    return fig, discarded


# ---------------------------------------------------------------------------
# the promise itself, with constrained_layout out of the way
# ---------------------------------------------------------------------------


def test_the_requested_width_is_the_rendered_width():
    # Arrange
    fig, _ = fr.subplots(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=False
    )
    # Act
    width_mm = _axes_size_mm(fig)[0]
    # Assert
    assert width_mm == pytest.approx(60.0, abs=0.01)


def test_the_requested_height_is_the_rendered_height():
    # Arrange
    fig, _ = fr.subplots(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=False
    )
    # Act
    height_mm = _axes_size_mm(fig)[1]
    # Assert
    assert height_mm == pytest.approx(20.0, abs=0.01)


def test_a_portrait_request_is_honoured_too():
    # Arrange: guards against a transposed-axis bug that a square would hide.
    fig, _ = fr.subplots(
        axes_width_mm=20, axes_height_mm=60, constrained_layout=False
    )
    # Act
    width_mm, height_mm = _axes_size_mm(fig)
    # Assert
    assert (width_mm, height_mm) == pytest.approx((20.0, 60.0), abs=0.01)


# ---------------------------------------------------------------------------
# and when it CANNOT be honoured, it must say so
# ---------------------------------------------------------------------------


def test_discarding_the_mm_request_is_announced():
    # Arrange: constrained_layout active + an explicit mm request is the case
    # where the caller asks for a size and silently does not get it.
    _, discarded = _subplots_capturing_warnings(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=True
    )
    # Act
    announced = bool(discarded)
    # Assert
    assert announced


def test_the_announcement_names_the_requested_size():
    # Arrange: an error that does not name the offending value is half-written.
    _, discarded = _subplots_capturing_warnings(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=True
    )
    # Act
    message = str(discarded[0].message)
    # Assert
    assert "60" in message and "20" in message


def test_the_announcement_says_what_to_do_about_it():
    # Arrange
    _, discarded = _subplots_capturing_warnings(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=True
    )
    # Act
    message = str(discarded[0].message)
    # Assert
    assert "constrained_layout=False" in message


def test_an_honoured_request_says_nothing():
    # Arrange: no warning when the mm actually lands, or it is just noise.
    _, discarded = _subplots_capturing_warnings(
        axes_width_mm=60, axes_height_mm=20, constrained_layout=False
    )
    # Act
    announced = bool(discarded)
    # Assert
    assert not announced


def test_style_supplied_defaults_do_not_warn():
    # Arrange: the caller asked for nothing, so nothing was taken from them.
    # Warning here would fire on every figure, and an always-on warning is
    # noise nobody reads.
    _, discarded = _subplots_capturing_warnings(constrained_layout=True)
    # Act
    announced = bool(discarded)
    # Assert
    assert not announced
