"""Tests for the font-consistency report.

THE MOST IMPORTANT TEST HERE IS THE FIRST ONE: a correctly styled figure must
report ZERO deviations. The operator's spec for this feature quotes "tick 6pt",
but the shipped style resolves ``tick_label_pt: 7`` — measured 2026-08-09. A
checker built on the quoted numbers would flag every correct figure's tick labels,
which is why expected sizes are read from ``get_style()["fonts"]`` instead. The
clean-figure test is what holds that decision in place: hardcode the spec again
and it goes red immediately.

One assertion per test, AAA markers.
"""

from __future__ import annotations

import warnings

import matplotlib
import pytest

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._quality._font_consistency import (
    ROLE_STYLE_KEY,
    check_font_consistency,
    font_consistency,
)


def _styled_figure():
    """A figure built entirely through figrecipe, touching every checked role."""
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 2, 1], label="series")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Title")
    ax.legend()
    return fig, ax


# ---------------------------------------------------------------------------
# the load-bearing property: silent on correct input
# ---------------------------------------------------------------------------


def test_a_correctly_styled_figure_has_no_deviations():
    # Arrange
    fig, _ = _styled_figure()
    # Act
    report = font_consistency(fig)
    # Assert
    assert report["deviations"] == []


def test_a_correctly_styled_figure_actually_checked_something():
    # Arrange: "no deviations" is worthless if it checked nothing — that is the
    # vacuous-pass shape this suite has been bitten by before.
    fig, _ = _styled_figure()
    # Act
    report = font_consistency(fig)
    # Assert
    assert report["checked"] > 5


def test_every_role_found_has_a_style_key():
    # Arrange: an unmapped role would be silently skipped, so it is reported.
    fig, _ = _styled_figure()
    # Act
    report = font_consistency(fig)
    # Assert
    assert report["unknown_roles"] == []


# ---------------------------------------------------------------------------
# and it must fail on bad input
# ---------------------------------------------------------------------------


def test_a_wrong_axis_label_size_is_reported():
    # Arrange: nothing in the style is 19pt.
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    report = font_consistency(fig)
    # Assert
    assert len(report["deviations"]) == 1


def test_the_deviation_names_the_actual_size():
    # Arrange
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    actual = font_consistency(fig)["deviations"][0]["actual_pt"]
    # Assert
    assert actual == 19.0


def test_the_deviation_names_the_expected_size():
    # Arrange: the report must carry what it SHOULD have been, not just that it
    # was wrong — an error that omits the expected value is half-written.
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    expected = font_consistency(fig)["deviations"][0]["expected_pt"]
    # Assert
    assert expected > 0


def test_the_deviation_names_the_role():
    # Arrange
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    role = font_consistency(fig)["deviations"][0]["role"]
    # Assert
    assert role == "axis_label"


def test_a_wrong_tick_size_is_reported():
    # Arrange: ticks are the numerous case, and the one the spec got wrong.
    fig, ax = _styled_figure()
    for lab in ax.get_xticklabels():
        lab.set_fontsize(19)
    # Act
    report = font_consistency(fig)
    # Assert
    assert len(report["deviations"]) > 0


# ---------------------------------------------------------------------------
# enforcement is opt-in
# ---------------------------------------------------------------------------


def test_strict_raises_on_a_deviation():
    # Arrange
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    act = lambda: check_font_consistency(fig, strict=True)  # noqa: E731
    # Assert
    with pytest.raises(ValueError):
        act()


def test_the_raised_message_names_the_offending_value():
    # Arrange
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    try:
        check_font_consistency(fig, strict=True)
        message = ""
    except ValueError as exc:
        message = str(exc)
    # Act
    names_it = "19.0pt" in message
    # Assert
    assert names_it


def test_strict_is_silent_on_a_correct_figure():
    # Arrange
    fig, _ = _styled_figure()
    # Act
    report = check_font_consistency(fig, strict=True)
    # Assert
    assert report["deviations"] == []


def test_the_default_warns_instead_of_raising():
    # Arrange: report-only by default; promoting figure violations to errors is
    # one coordinated decision, not a per-module switch.
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    # Act
    act = lambda: check_font_consistency(fig)  # noqa: E731
    # Assert
    with pytest.warns(UserWarning):
        act()


def test_the_default_still_returns_the_deviations():
    # Arrange: warning instead of raising must not cost the caller the data.
    fig, ax = _styled_figure()
    ax.xaxis.label.set_fontsize(19)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        report = check_font_consistency(fig)
    # Act
    found = len(report["deviations"])
    # Assert
    assert found == 1


# ---------------------------------------------------------------------------
# the role map itself
# ---------------------------------------------------------------------------


def test_the_role_map_covers_tick_labels():
    # Arrange: the role the spec got wrong must be mapped, not omitted.
    expected_key = "tick_label_pt"
    # Act
    actual_key = ROLE_STYLE_KEY.get("tick_label")
    # Assert
    assert actual_key == expected_key
