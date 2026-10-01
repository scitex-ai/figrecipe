"""Tests for the composed-figure width warning (over-wide -> silent \\resizebox).

Real matplotlib figures, no mocks. One assertion per test, AAA markers.
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from figrecipe._quality._compose_width import (
    COMPOSE_MAX_WIDTH_MM,
    check_compose_width,
    figure_width_mm,
)

MM_PER_INCH = 25.4


@pytest.fixture
def wide_fig():
    """A figure comfortably wider than the 180mm text block."""
    fig = plt.figure(figsize=(300 / MM_PER_INCH, 100 / MM_PER_INCH))
    yield fig
    plt.close(fig)


@pytest.fixture
def narrow_fig():
    """A figure that fits the text block."""
    fig = plt.figure(figsize=(120 / MM_PER_INCH, 80 / MM_PER_INCH))
    yield fig
    plt.close(fig)


# ---------------------------------------------------------------------------
# width measurement
# ---------------------------------------------------------------------------


def test_reports_width_in_millimetres(narrow_fig):
    # Arrange
    expected = 120.0
    # Act
    actual = figure_width_mm(narrow_fig)
    # Assert
    assert actual == pytest.approx(expected, abs=0.5)


def test_returns_none_for_an_object_with_no_size(narrow_fig):
    # Arrange
    not_a_figure = object()
    # Act
    actual = figure_width_mm(not_a_figure)
    # Assert
    assert actual is None


# ---------------------------------------------------------------------------
# the warning
# ---------------------------------------------------------------------------


def test_warns_when_wider_than_the_text_block(wide_fig):
    # Arrange
    limit = COMPOSE_MAX_WIDTH_MM
    # Act
    # Assert
    with pytest.warns(UserWarning, match="exceeds 180mm"):
        check_compose_width(wide_fig, max_width_mm=limit)


def test_warning_names_resizebox_as_the_consequence(wide_fig):
    # Arrange
    limit = COMPOSE_MAX_WIDTH_MM
    # Act
    # Assert
    with pytest.warns(UserWarning, match=r"resizebox"):
        check_compose_width(wide_fig, max_width_mm=limit)


def test_warning_says_text_is_shrunk_too(wide_fig):
    # Arrange: the reader must learn WHY an over-wide figure matters — the
    # text scaling is the damage, not the width itself.
    limit = COMPOSE_MAX_WIDTH_MM
    # Act
    # Assert
    with pytest.warns(UserWarning, match="including its TEXT"):
        check_compose_width(wide_fig, max_width_mm=limit)


def test_reports_pixels_when_a_dpi_is_supplied(wide_fig):
    # Arrange
    dpi = 300
    # Act
    # Assert
    with pytest.warns(UserWarning, match="px at 300dpi"):
        check_compose_width(wide_fig, dpi=dpi)


def test_returns_the_measured_width_when_it_warns(wide_fig):
    # Arrange
    limit = COMPOSE_MAX_WIDTH_MM
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        actual = check_compose_width(wide_fig, max_width_mm=limit)
    # Assert
    assert actual == pytest.approx(300.0, abs=0.5)


# ---------------------------------------------------------------------------
# silence — the cases that must NOT warn
# ---------------------------------------------------------------------------


def test_does_not_warn_when_it_fits(narrow_fig):
    # Arrange
    limit = COMPOSE_MAX_WIDTH_MM
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_width(narrow_fig, max_width_mm=limit)
    # Assert
    assert caught == []


def test_does_not_warn_exactly_at_the_limit():
    # Arrange: the boundary must be inclusive — a figure sized exactly to the
    # text width is the CORRECT answer, not a violation.
    fig = plt.figure(figsize=(COMPOSE_MAX_WIDTH_MM / MM_PER_INCH, 2.0))
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_width(fig)
    plt.close(fig)
    # Assert
    assert caught == []


def test_does_not_warn_when_the_width_is_unknown():
    # Arrange: an unknown width is reported as unknown, never assumed to be a
    # violation — a quality check must not invent a finding.
    not_a_figure = object()
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_width(not_a_figure)
    # Assert
    assert caught == []


def test_returns_none_when_the_width_is_unknown():
    # Arrange
    not_a_figure = object()
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        actual = check_compose_width(not_a_figure)
    # Assert
    assert actual is None


def test_a_raised_limit_silences_a_wide_figure(wide_fig):
    # Arrange: a project whose page is genuinely wider passes its own limit.
    limit = 400.0
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_width(wide_fig, max_width_mm=limit)
    # Assert
    assert caught == []
