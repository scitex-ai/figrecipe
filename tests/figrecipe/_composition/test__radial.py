#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._composition._radial (p5js-ported layout helpers).

Card figrecipe-bioinformatics-figure-beauty-20261006, source-adoption phase:
deterministic radial placement + Poisson-disk sampling, ported from the p5js
skill references (core-api.md radial layout, visual-effects.md Poisson-disk)
and proven in PoC3. NumPy only, no engine dependency.
"""

import numpy as np

from figrecipe._composition._radial import poisson_disk, radial_positions


class TestRadialPositions:
    def test_six_points_are_evenly_spaced_on_the_circle(self):
        # Arrange
        # Act
        pts = radial_positions(6)
        # Assert -- adjacent angles differ by exactly 2*pi/6.
        angs = np.sort(np.arctan2(pts[:, 1], pts[:, 0]))
        gaps = np.diff(np.append(angs, angs[0] + 2 * np.pi))
        assert np.allclose(gaps, 2 * np.pi / 6)


class TestPoissonDisk:
    def test_same_seed_gives_same_points(self):
        # Arrange
        # Act
        a = poisson_disk(2.0, 2.0, 0.3, seed=7)
        b = poisson_disk(2.0, 2.0, 0.3, seed=7)
        # Assert -- determinism is the contract (recipe reproducibility).
        assert np.array_equal(a, b)

    def test_points_keep_the_minimum_distance(self):
        # Arrange
        # Act
        pts = poisson_disk(2.0, 2.0, 0.3, seed=7)
        # Assert -- every pair is at least min_dist apart.
        d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
        iu = np.triu_indices(len(pts), k=1)
        assert bool(np.all(d[iu] >= 0.3 - 1e-9))
