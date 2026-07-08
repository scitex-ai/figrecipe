#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the save-time layout-conflict (overlap) detector.

One test per policy-table cell. AAA layout, ONE assertion each, no mocks,
headless Agg backend. Each test drives ``detect_layout_conflicts`` directly
on a real matplotlib figure and asserts whether a matching conflict was
produced (presence/absence of the relevant role-pair).
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from figrecipe._quality._overlap import detect_layout_conflicts  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figs():
    # Arrange / teardown: keep the pyplot state clean between tests.
    yield
    plt.close("all")


def _has_pair(conflicts, role_a, role_b):
    """True if any conflict matches the unordered role pair."""
    want = {role_a, role_b}
    return any({c.role_a, c.role_b} == want for c in conflicts)


# ---------------------------------------------------------------------------
# (legend, ink) -> forbidden
# ---------------------------------------------------------------------------
def test_legend_over_line_warns():
    # Arrange
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot(np.linspace(0, 1, 50), np.linspace(0, 1, 50), lw=2)
    ax.legend(["line"], loc="center")
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_pair(conflicts, "legend", "ink")


def test_legend_over_blank_silent():
    # Arrange
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0.0, 0.2], [0.0, 0.2], lw=2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(["line"], loc="upper right")
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert not _has_pair(conflicts, "legend", "ink")


# ---------------------------------------------------------------------------
# (text, ink) -> allowed (intentional callouts)
# ---------------------------------------------------------------------------
def test_text_annotation_over_line_silent():
    # Arrange
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot(np.linspace(0, 1, 50), np.linspace(0, 1, 50), lw=2)
    ax.annotate("peak", xy=(0.5, 0.5), xytext=(0.5, 0.5))
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert not _has_pair(conflicts, "text", "ink")


# ---------------------------------------------------------------------------
# (text, text) -> forbidden
# ---------------------------------------------------------------------------
def test_two_overlapping_texts_warn():
    # Arrange
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, "AAAAA", ha="center", va="center", fontsize=20)
    ax.text(0.5, 0.5, "BBBBB", ha="center", va="center", fontsize=20)
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_pair(conflicts, "text", "text")


def test_two_overlapping_annotations_warn():
    # Arrange: ax.annotate makes an Annotation (a Text SUBCLASS); it must not
    # slip past the text enumeration the way an exact class-name check let it.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.annotate("P01", xy=(0.5, 0.5), ha="center", va="center", fontsize=20)
    ax.annotate("P02", xy=(0.5, 0.5), ha="center", va="center", fontsize=20)
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_pair(conflicts, "text", "text")


# ---------------------------------------------------------------------------
# (colorbar, axes) -> forbidden
# ---------------------------------------------------------------------------
def test_colorbar_over_tile_warns():
    # Arrange: colorbar cax explicitly positioned on top of the data axes.
    fig = plt.figure(figsize=(4, 3), dpi=100)
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    im = ax.imshow(np.random.rand(5, 5))
    cax = fig.add_axes([0.35, 0.3, 0.06, 0.4])  # overlaps the data axes
    fig.colorbar(im, cax=cax)
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_pair(conflicts, "colorbar", "axes")


def test_colorbar_clear_to_right_silent():
    # Arrange: single axes, colorbar in its own stolen strip to the right.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    im = ax.imshow(np.random.rand(4, 4))
    fig.colorbar(im, ax=ax)
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert not _has_pair(conflicts, "colorbar", "axes")


# ---------------------------------------------------------------------------
# (axes, axes) -> forbidden
# ---------------------------------------------------------------------------
def test_two_axes_overlapping_warn():
    # Arrange: a second data axes placed on top via manual add_axes.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    fig.add_axes([0.3, 0.3, 0.4, 0.4])
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert _has_pair(conflicts, "axes", "axes")


def test_overlapping_lines_one_axes_silent():
    # Arrange: two crossing lines share one axes -> (ink, ink) is allowed.
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.plot([0, 1], [0, 1], lw=2)
    ax.plot([0, 1], [1, 0], lw=2)
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert conflicts == []


def test_flush_adjacent_panels_silent():
    # Arrange: shared-edge grid with zero gap (no whitespace between panels).
    fig, axs = plt.subplots(1, 3, figsize=(6, 2), dpi=100)
    fig.subplots_adjust(wspace=0.0)
    for ax in axs:
        ax.plot([0, 1], [0, 1])
    # Act
    conflicts = detect_layout_conflicts(fig)
    # Assert
    assert not _has_pair(conflicts, "axes", "axes")


# ---------------------------------------------------------------------------
# ink mask: Text subclasses (Annotation) are NOT counted as data ink
# ---------------------------------------------------------------------------
def test_annotation_not_counted_as_data_ink():
    # Arrange -- an annotation in empty axes space. The data-only ink mask must
    # hide it (Annotation is a Text subclass), so its bbox holds ~no ink; an
    # exact class-name check leaked the annotation pixels into the mask.
    from figrecipe._quality._overlap_ink import (
        _ink_fraction_in_bbox,
        _render_ink_mask,
    )

    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ann = ax.annotate("XXXXXX", xy=(0.5, 0.5), ha="center", va="center", fontsize=24)
    fig.canvas.draw()
    bbox = ann.get_window_extent(renderer=fig._get_renderer())
    mask, height = _render_ink_mask(fig, None)
    # Act
    frac = _ink_fraction_in_bbox(mask, height, bbox)
    # Assert
    assert frac < 0.02


# EOF
