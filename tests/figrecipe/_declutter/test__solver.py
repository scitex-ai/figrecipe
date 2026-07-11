#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the deterministic label-repel solver (pure geometry)."""

import numpy as np

from figrecipe._declutter._solver import _overlap_fraction, solve_label_positions


def _no_ink(size=200):
    return np.zeros((size, size), dtype=bool), size


def _all_ink(size=200):
    return np.ones((size, size), dtype=bool), size


def _box(center, half_w=10, half_h=5):
    cx, cy = center
    return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)


def test_single_label_sits_at_clear_anchor():
    # Arrange
    ink, h = _no_ink()
    # Act
    centers, clear = solve_label_positions([(100.0, 100.0)], [(20.0, 10.0)], ink, h)
    # Assert
    assert centers == [(100.0, 100.0)] and clear == [True]


def test_two_labels_same_anchor_do_not_overlap():
    # Arrange
    ink, h = _no_ink()
    anchors = [(100.0, 100.0), (100.0, 100.0)]
    sizes = [(20.0, 10.0), (20.0, 10.0)]
    # Act
    centers, clear = solve_label_positions(anchors, sizes, ink, h)
    overlap = _overlap_fraction(_box(centers[0]), _box(centers[1]))
    # Assert
    assert clear == [True, True] and overlap == 0.0


def test_deterministic_same_inputs_same_output():
    # Arrange
    ink, h = _no_ink()
    anchors = [(50.0, 50.0), (50.0, 50.0), (60.0, 55.0)]
    sizes = [(18.0, 9.0)] * 3
    # Act
    first, second = (
        solve_label_positions(anchors, sizes, ink, h),
        solve_label_positions(anchors, sizes, ink, h),
    )
    # Assert
    assert first == second


def test_label_avoids_ink_lands_in_clear_patch():
    # Arrange -- everything is ink except a clear patch to the right.
    ink, h = _all_ink()
    ink[40:60, 150:170] = False  # display y in [140,160], x in [150,170]
    clip = (0.0, 0.0, 200.0, 200.0)
    # Act
    centers, clear = solve_label_positions(
        [(100.0, 150.0)], [(10.0, 10.0)], ink, h, clip_rect=clip
    )
    # Assert -- pushed to the right, into the clear patch.
    assert clear == [True] and centers[0][0] > 100.0


def test_no_clear_spot_falls_back_to_anchor_flagged():
    # Arrange -- fully inked, clipped: nowhere clear.
    ink, h = _all_ink()
    clip = (0.0, 0.0, 200.0, 200.0)
    # Act
    centers, clear = solve_label_positions(
        [(100.0, 100.0)], [(10.0, 10.0)], ink, h, clip_rect=clip
    )
    # Assert
    assert centers == [(100.0, 100.0)] and clear == [False]


def test_obstacle_box_is_avoided():
    # Arrange -- a legend-like obstacle sits on the up direction.
    ink, h = _no_ink()
    obstacle = (85.0, 100.0, 135.0, 140.0)  # covers up / up-right of the anchor
    # Act
    centers, clear = solve_label_positions(
        [(100.0, 100.0)], [(20.0, 10.0)], ink, h, obstacles=[obstacle]
    )
    overlap = _overlap_fraction(_box(centers[0]), obstacle)
    # Assert
    assert clear == [True] and overlap == 0.0
