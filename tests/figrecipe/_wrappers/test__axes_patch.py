#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for ``_wrappers/_axes_patch.serialize_patch``.

Deterministic (no rendering): they check the {patch_class, geom, props}
descriptor captured for each handled patch class and the generic fallback.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches

from figrecipe._wrappers._axes_patch import serialize_patch


def test_serialize_rectangle_captures_class_and_geometry():
    # Arrange
    patch = mpatches.Rectangle((0.2, 0.3), 0.6, 0.4, angle=10)
    # Act
    descriptor = serialize_patch(patch)
    geom = descriptor["geom"]
    # Assert
    assert (
        descriptor["patch_class"],
        geom["xy"],
        geom["width"],
        geom["height"],
        geom["angle"],
    ) == ("Rectangle", [0.2, 0.3], 0.6, 0.4, 10.0)


def test_serialize_circle_captures_center_and_radius():
    # Arrange
    patch = mpatches.Circle((1.0, 2.0), 0.5)
    # Act
    descriptor = serialize_patch(patch)
    # Assert
    assert (
        descriptor["patch_class"],
        descriptor["geom"]["xy"],
        descriptor["geom"]["radius"],
    ) == ("Circle", [1.0, 2.0], 0.5)


def test_serialize_polygon_captures_vertices():
    # Arrange
    patch = mpatches.Polygon([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])
    # Act
    descriptor = serialize_patch(patch)
    # Assert
    assert (descriptor["patch_class"], descriptor["geom"]["xy"][:3]) == (
        "Polygon",
        [[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]],
    )


def test_serialize_unknown_patch_falls_back_to_pathpatch():
    # Arrange -- FancyBboxPatch is not a handled class
    patch = mpatches.FancyBboxPatch((0.0, 0.0), 1.0, 1.0, boxstyle="round")
    # Act
    descriptor = serialize_patch(patch)
    # Assert -- generic path fallback, with data-space vertices captured
    assert (
        descriptor["patch_class"],
        len(descriptor["geom"]["path_vertices"]) > 0,
    ) == (
        "PathPatch",
        True,
    )


def test_serialize_folds_alpha_into_facecolor():
    # Arrange
    patch = mpatches.Rectangle((0, 0), 1, 1, facecolor="orange", alpha=0.5)
    # Act
    descriptor = serialize_patch(patch)
    # Assert -- alpha lives in the rgba 4th channel (no separate, double-applied key)
    assert round(descriptor["props"]["facecolor"][3], 3) == 0.5
