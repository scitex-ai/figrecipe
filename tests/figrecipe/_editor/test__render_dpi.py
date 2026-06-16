#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for render_with_overrides DPI handling.

The editor preview used to render at a fixed 150 dpi while the canvas/ruler use
the display DPI, so a 180 mm figure drew ~1.57x wider than the 180 mm ruler
mark. render_with_overrides now takes a dpi (the canvas display DPI), and
remembers it on the figure so subsequent edit re-renders keep the same size.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._editor._helpers import render_with_overrides


class TestRenderDpi:
    def test_lower_dpi_yields_smaller_image(self):
        # Arrange
        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        # Act
        _, _, size150 = render_with_overrides(fig, {}, False, dpi=150)
        _, _, size96 = render_with_overrides(fig, {}, False, dpi=96)
        # Assert -- pixel width scales with dpi (so it can match the mm ruler)
        assert size96[0] < size150[0]

    def test_dpi_ratio_matches_request(self):
        # Arrange
        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        # Act
        _, _, size150 = render_with_overrides(fig, {}, False, dpi=150)
        _, _, size75 = render_with_overrides(fig, {}, False, dpi=75)
        # Assert -- halving the dpi roughly halves the pixel width (±2 px rounding)
        assert abs(size150[0] - 2 * size75[0]) <= 2

    def test_explicit_dpi_is_remembered_for_later_renders(self):
        # Arrange -- entry points pass dpi; edit handlers then call with dpi=None
        # and must keep the same size (else the figure resizes mid-edit).
        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        _, _, size96 = render_with_overrides(fig, {}, False, dpi=96)
        # Act
        _, _, size_default = render_with_overrides(fig, {}, False)
        # Assert
        assert size_default == size96
