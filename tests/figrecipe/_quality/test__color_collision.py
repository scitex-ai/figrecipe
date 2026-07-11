#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the save-time COLOR-collision detector.

AAA layout, ONE assertion each, no mocks, headless Agg backend. Each test
drives ``detect_color_collisions`` (or the color-science helper
``delta_e76``) directly on a real matplotlib figure and asserts whether a
color-collision Conflict was produced.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe._quality._color_collision import (  # noqa: E402
    delta_e76,
    detect_color_collisions,
)
from figrecipe._quality._overlap import detect_layout_conflicts  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figs():
    # Arrange / teardown: keep the pyplot state clean between tests.
    yield
    plt.close("all")


def _has_color(conflicts):
    """True if any conflict is a color collision."""
    return any(c.kind == "color" for c in conflicts)


# ---------------------------------------------------------------------------
# Color science: sRGB -> CIELAB ΔE*76
# ---------------------------------------------------------------------------
def test_delta_e_zero_for_identical_colors():
    # Arrange
    color = (0.12, 0.47, 0.71)
    # Act
    de = delta_e76(color, color)
    # Assert
    assert de == pytest.approx(0.0, abs=1e-9)


def test_delta_e_red_vs_blue_is_large():
    # Arrange
    red, blue = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    # Act
    de = delta_e76(red, blue)
    # Assert
    assert de > 100.0


# ---------------------------------------------------------------------------
# detect_color_collisions
# ---------------------------------------------------------------------------
def test_near_identical_line_colors_flagged():
    # Arrange: two labelled lines whose colors differ imperceptibly.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    ax.plot([0, 1], [1, 0], color="#1f77b6", label="B")
    # Act
    conflicts = detect_color_collisions([ax])
    # Assert
    assert _has_color(conflicts)


def test_distinct_line_colors_not_flagged():
    # Arrange: two clearly distinguishable labelled lines.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="red", label="A")
    ax.plot([0, 1], [1, 0], color="blue", label="B")
    # Act
    conflicts = detect_color_collisions([ax])
    # Assert
    assert not _has_color(conflicts)


def test_unlabelled_near_identical_lines_not_flagged():
    # Arrange: same near-duplicate colors but NO legend labels -> not a series
    # a reader is asked to distinguish, so it must stay silent.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="#1f77b4")
    ax.plot([0, 1], [1, 0], color="#1f77b6")
    # Act
    conflicts = detect_color_collisions([ax])
    # Assert
    assert not _has_color(conflicts)


def test_same_label_same_color_not_flagged():
    # Arrange: one logical series drawn in two segments (same label) -- the
    # identical color is intentional, never a collision.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    ax.plot([1, 2], [1, 2], color="#1f77b4", label="A")
    # Act
    conflicts = detect_color_collisions([ax])
    # Assert
    assert not _has_color(conflicts)


def test_colormapped_scatter_not_flagged():
    # Arrange: a colormapped scatter carries many colors on purpose; its
    # gradient must never be read as a near-duplicate collision.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.scatter([0, 1, 2], [0, 1, 2], c=[0, 1, 2], cmap="viridis", label="pts")
    ax.plot([0, 2], [0, 2], color="#1f77b4", label="line")
    # Act
    conflicts = detect_color_collisions([ax])
    # Assert
    assert not _has_color(conflicts)


def test_near_identical_colors_across_panels_not_flagged():
    # Arrange: the SAME color reused in two separate panels is fine -- only
    # within-axes ambiguity matters.
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(6, 3), dpi=100)
    ax0.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    ax1.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    # Act
    conflicts = detect_color_collisions([ax0, ax1])
    # Assert
    assert not _has_color(conflicts)


# ---------------------------------------------------------------------------
# Conflict payload + save-time integration
# ---------------------------------------------------------------------------
def test_color_conflict_describe_mentions_delta_e():
    # Arrange
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    ax.plot([0, 1], [1, 0], color="#1f77b6", label="B")
    # Act
    text = detect_color_collisions([ax])[0].describe()
    # Assert
    assert "ΔE" in text


def test_run_overlap_check_surfaces_color_collision():
    # Arrange: the save-time entry point must fold color collisions in.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], color="#1f77b4", label="A")
    ax.plot([0, 1], [1, 0], color="#1f77b6", label="B")
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_color(conflicts)


# EOF
