"""Tests for the composed-figure whitespace measurement and opt-in threshold.

Real matplotlib figures, no mocks. One assertion per test, AAA markers.

The operator's ask (via neurovista): return the whitespace ratio, and set a
threshold so an over-sparse composite errors rather than plots. Enforcement is
opt-in; these tests pin BOTH halves — that it measures, and that it stays quiet
until asked to enforce.
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from figrecipe._quality._compose_whitespace import (
    NOTEWORTHY_WHITESPACE_FRAC,
    check_compose_whitespace,
    compose_whitespace,
)


@pytest.fixture
def sparse_fig():
    """A figure with one small axes, so most of the canvas is blank."""
    fig = plt.figure(figsize=(6, 6))
    fig.add_axes([0.05, 0.05, 0.2, 0.2])
    yield fig
    plt.close(fig)


@pytest.fixture
def full_fig():
    """A figure whose axes covers almost the whole canvas."""
    fig = plt.figure(figsize=(6, 6))
    fig.add_axes([0.0, 0.0, 1.0, 1.0])
    yield fig
    plt.close(fig)


def _quiet(fn, *a, **kw):
    """Run without letting the advisory warning escape into the assertion."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fn(*a, **kw)


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------


def test_reports_high_whitespace_for_a_sparse_figure(sparse_fig):
    # Arrange
    floor = 0.5
    # Act
    measured = compose_whitespace(sparse_fig)
    # Assert
    assert measured["whitespace_frac"] > floor


def test_reports_low_whitespace_for_a_full_figure(full_fig):
    # Arrange
    ceiling = 0.2
    # Act
    measured = compose_whitespace(full_fig)
    # Assert
    assert measured["whitespace_frac"] < ceiling


def test_whitespace_is_the_complement_of_coverage(sparse_fig):
    # Arrange: whitespace is DERIVED from layout_report's coverage_frac rather
    # than measured separately, so the two must agree exactly.
    measured = compose_whitespace(sparse_fig)
    # Act
    total = measured["whitespace_frac"] + measured["coverage_frac"]
    # Assert
    assert total == pytest.approx(1.0)


def test_reports_the_empty_regions(sparse_fig):
    # Arrange
    measured = compose_whitespace(sparse_fig)
    # Act
    regions = measured["empty_regions"]
    # Assert
    assert regions != []


def test_returns_none_when_the_layout_cannot_be_read():
    # Arrange: unknown is reported as unknown, never defaulted to zero — which
    # would read as "perfectly packed".
    not_a_figure = object()
    # Act
    measured = compose_whitespace(not_a_figure)
    # Assert
    assert measured is None


# ---------------------------------------------------------------------------
# enforcement — opt-in
# ---------------------------------------------------------------------------


def test_raises_above_an_explicit_threshold(sparse_fig):
    # Arrange
    limit = 0.1
    # Act
    # Assert
    with pytest.raises(ValueError, match="FR-COMPOSE-WHITESPACE"):
        _quiet(check_compose_whitespace, sparse_fig, max_whitespace_frac=limit)


def test_the_refusal_names_the_measured_figure(sparse_fig):
    # Arrange
    limit = 0.1
    # Act
    # Assert
    with pytest.raises(ValueError, match=r"\d+% blank"):
        _quiet(check_compose_whitespace, sparse_fig, max_whitespace_frac=limit)


def test_the_refusal_points_at_the_blank_regions(sparse_fig):
    # Arrange
    limit = 0.1
    # Act
    # Assert
    with pytest.raises(ValueError, match="largest blank regions"):
        _quiet(check_compose_whitespace, sparse_fig, max_whitespace_frac=limit)


def test_does_not_raise_below_the_threshold(sparse_fig):
    # Arrange: a generous limit must permit the same figure.
    limit = 0.99
    # Act
    measured = _quiet(check_compose_whitespace, sparse_fig, max_whitespace_frac=limit)
    # Assert
    assert measured["whitespace_frac"] < limit


def test_a_full_figure_passes_a_strict_threshold(full_fig):
    # Arrange
    limit = 0.2
    # Act
    measured = _quiet(check_compose_whitespace, full_fig, max_whitespace_frac=limit)
    # Assert
    assert measured is not None


# ---------------------------------------------------------------------------
# the default: measure, do not enforce. A raising default would break every
# existing sparse composite at once.
# ---------------------------------------------------------------------------


def test_no_threshold_means_no_exception(sparse_fig):
    # Arrange
    limit = None
    # Act
    measured = _quiet(check_compose_whitespace, sparse_fig, max_whitespace_frac=limit)
    # Assert
    assert measured is not None


def test_a_very_sparse_figure_still_warns_without_a_threshold(sparse_fig):
    # Arrange: silence is not the default either — over half blank is worth
    # saying out loud, just not worth refusing.
    limit = None
    # Act
    # Assert
    with pytest.warns(UserWarning, match="blank"):
        check_compose_whitespace(sparse_fig, max_whitespace_frac=limit)


def test_a_full_figure_does_not_warn_without_a_threshold(full_fig):
    # Arrange
    limit = None
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_whitespace(full_fig, max_whitespace_frac=limit)
    # Assert
    assert caught == []


def test_the_noteworthy_line_is_half_the_canvas():
    # Arrange: pinned because the advisory warning's threshold is a documented
    # choice, not an implementation detail.
    expected = 0.5
    # Act
    actual = NOTEWORTHY_WHITESPACE_FRAC
    # Assert
    assert actual == expected


def test_an_unreadable_figure_neither_warns_nor_raises():
    # Arrange
    not_a_figure = object()
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_compose_whitespace(not_a_figure, max_whitespace_frac=0.0)
    # Assert
    assert caught == []
