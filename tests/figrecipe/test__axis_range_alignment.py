#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the runtime ``axis_range_alignment`` validator.

These tests build real matplotlib ``Figure`` objects (no mocks) and
call the validator directly. ``matplotlib.use("Agg")`` is already set
by the root ``conftest.py``; we still set it here defensively in case
this file is run in isolation.
"""

from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from figrecipe._axis_range_alignment import (  # noqa: E402
    WARNING_MESSAGE,
    check_axis_range_alignment,
    run_axis_range_alignment,
)

# ---------------------------------------------------------------------------
# POSITIVE — fires
# ---------------------------------------------------------------------------


def test_mismatched_ylim_with_shared_ylabel_triggers():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is True

    plt.close(fig)


def test_mismatched_ylim_emits_warning_at_default_level():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)

    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        run_axis_range_alignment(fig)
    triggering_messages = [
        str(w.message) for w in caught if WARNING_MESSAGE in str(w.message)
    ]

    # Assert
    assert len(triggering_messages) == 1

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — does not fire when ranges agree
# ---------------------------------------------------------------------------


def test_matching_ylim_with_shared_ylabel_does_not_trigger():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 1)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — matplotlib sharey=True
# ---------------------------------------------------------------------------


def test_sharey_true_skips_the_check_for_y_axis():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2, sharey=True)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    # With sharey=True, both calls effectively pin the same limit, so
    # by construction get_ylim() agrees on both axes — but more
    # importantly the validator must skip y-axis comparison entirely.
    ax0.set_ylim(0, 1)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — different ylabels (peers don't share a quantity)
# ---------------------------------------------------------------------------


def test_different_ylabels_are_not_grouped_as_peers():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("current")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — twinx
# ---------------------------------------------------------------------------


def test_twinx_axes_are_skipped_by_design():
    # Arrange
    fig, ax = plt.subplots()
    ax.set_ylabel("voltage")
    ax2 = ax.twinx()
    ax2.set_ylabel("voltage")
    ax.set_ylim(0, 1)
    ax2.set_ylim(0, 5)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — opt-out sentinel
# ---------------------------------------------------------------------------


def test_opt_out_sentinel_skips_the_check_entirely():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)
    fig._figrecipe_allow_axis_mismatch = True

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# NEGATIVE — single axis (no comparison possible)
# ---------------------------------------------------------------------------


def test_single_axis_figure_is_a_noop():
    # Arrange
    fig, ax = plt.subplots(1, 1)
    ax.set_ylabel("voltage")
    ax.set_ylim(0, 1)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# ---------------------------------------------------------------------------
# Extra edge cases
# ---------------------------------------------------------------------------


def test_mismatched_xlim_with_shared_xlabel_triggers():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(2, 1)
    ax0.set_xlabel("time (s)")
    ax1.set_xlabel("time (s)")
    ax0.set_xlim(0, 1)
    ax1.set_xlim(0, 10)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is True

    plt.close(fig)


def test_error_level_raises_value_error_when_mismatched():
    # Arrange

    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)
    raised = False

    # Act
    try:
        run_axis_range_alignment(fig, validate_error_level="error")
    except ValueError:
        raised = True

    # Assert
    assert raised is True

    plt.close(fig)


def test_debug_level_is_silent_when_mismatched():
    # Arrange
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)

    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        run_axis_range_alignment(fig, validate_error_level="debug")
    triggering = [w for w in caught if WARNING_MESSAGE in str(w.message)]

    # Assert
    assert triggering == []

    plt.close(fig)


def test_empty_labels_without_gridspec_skip_the_axis():
    # Arrange — create two bare axes with no labels and no shared
    # gridspec. The validator must NOT warn (cannot infer peers).
    fig = plt.figure()
    ax0 = fig.add_axes([0.1, 0.1, 0.35, 0.8])
    ax1 = fig.add_axes([0.55, 0.1, 0.35, 0.8])
    ax0.set_ylim(0, 1)
    ax1.set_ylim(0, 5)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


def test_two_dot_five_percent_tolerance_does_trigger():
    # Arrange — well outside the 1e-3 rel_tol tolerance.
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0.0, 1.0)
    ax1.set_ylim(0.0, 1.025)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is True

    plt.close(fig)


def test_within_tolerance_does_not_trigger():
    # Arrange — inside the 1e-3 rel_tol tolerance.
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax0.set_ylabel("voltage")
    ax1.set_ylabel("voltage")
    ax0.set_ylim(0.0, 1.0)
    ax1.set_ylim(0.0, 1.0 + 1e-6)

    # Act
    result = check_axis_range_alignment(fig)

    # Assert
    assert result.triggered is False

    plt.close(fig)


# EOF
