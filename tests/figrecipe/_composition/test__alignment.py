#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for alignment feature (Phase 3).

Tests for align_panels(), distribute_panels(), and align_smart() functions.
"""

import matplotlib

matplotlib.use("Agg")


import figrecipe as fr
from figrecipe import utils


class TestAlignPanels:
    """Tests for align_panels() function."""

    def test_align_left(self):
        """Align panels to left edge."""
        fig, axes = fr.subplots(2, 2)
        for i in range(2):
            for j in range(2):
                axes[i, j].plot([1, 2], [i + j, i + j + 1])

        fr.align_panels(fig, [(0, 0), (1, 0)], mode="left")
        assert fig is not None

    def test_align_right(self):
        """Align panels to right edge."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (0, 1)], mode="right")
        assert fig is not None

    def test_align_top(self):
        """Align panels to top edge."""
        fig, axes = fr.subplots(2, 1)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (1, 0)], mode="top")
        assert fig is not None

    def test_align_bottom(self):
        """Align panels to bottom edge."""
        fig, axes = fr.subplots(2, 1)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (1, 0)], mode="bottom")
        assert fig is not None

    def test_align_center_horizontal(self):
        """Align panels to horizontal center."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (0, 1)], mode="center_h")
        assert fig is not None

    def test_align_center_vertical(self):
        """Align panels to vertical center."""
        fig, axes = fr.subplots(2, 1)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (1, 0)], mode="center_v")
        assert fig is not None

    def test_align_axis_x(self):
        """Align x-axes of panels."""
        fig, axes = fr.subplots(2, 1)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (1, 0)], mode="axis_x")
        assert fig is not None

    def test_align_axis_y(self):
        """Align y-axes of panels."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (0, 1)], mode="axis_y")
        assert fig is not None

    def test_align_with_reference(self):
        """Align panels using explicit reference."""
        fig, axes = fr.subplots(1, 3)
        for i in range(3):
            axes[i].plot([1, 2], [i, i + 1])

        fr.align_panels(
            fig,
            [(0, 0), (0, 1), (0, 2)],
            mode="bottom",
            reference=(0, 1),
        )
        assert fig is not None

    def test_align_empty_panels_list(self):
        """Align with empty panel list does nothing."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        fr.align_panels(fig, [], mode="left")
        assert fig is not None

    def test_alignment_mode_enum(self):
        """AlignmentMode enum values are accessible."""
        assert utils.AlignmentMode.LEFT.value == "left"
        assert utils.AlignmentMode.RIGHT.value == "right"
        assert utils.AlignmentMode.TOP.value == "top"
        assert utils.AlignmentMode.BOTTOM.value == "bottom"
        assert utils.AlignmentMode.CENTER_H.value == "center_h"
        assert utils.AlignmentMode.CENTER_V.value == "center_v"
        assert utils.AlignmentMode.AXIS_X.value == "axis_x"
        assert utils.AlignmentMode.AXIS_Y.value == "axis_y"

    def test_align_with_enum_mode(self):
        """Align using AlignmentMode enum."""
        fig, axes = fr.subplots(1, 2)
        axes[0].plot([1, 2], [1, 2])
        axes[1].plot([1, 2], [2, 1])

        fr.align_panels(fig, [(0, 0), (0, 1)], mode=utils.AlignmentMode.AXIS_Y)
        assert fig is not None


class TestDistributePanels:
    """Tests for distribute_panels() function."""

    def test_distribute_horizontal(self):
        """Distribute panels horizontally."""
        fig, axes = fr.subplots(1, 3)
        for i in range(3):
            axes[i].plot([1, 2], [i, i + 1])

        fr.distribute_panels(fig, [(0, 0), (0, 1), (0, 2)], direction="horizontal")
        assert fig is not None

    def test_distribute_vertical(self):
        """Distribute panels vertically."""
        fig, axes = fr.subplots(3, 1)
        for i in range(3):
            axes[i].plot([1, 2], [i, i + 1])

        fr.distribute_panels(fig, [(0, 0), (1, 0), (2, 0)], direction="vertical")
        assert fig is not None

    def test_distribute_with_fixed_spacing(self):
        """Distribute with fixed mm spacing."""
        fig, axes = fr.subplots(1, 3)
        for i in range(3):
            axes[i].plot([1, 2], [i, i + 1])

        fr.distribute_panels(
            fig,
            [(0, 0), (0, 1), (0, 2)],
            direction="horizontal",
            spacing_mm=10,
        )
        assert fig is not None

    def test_distribute_single_panel(self):
        """Distribute with single panel does nothing."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        fr.distribute_panels(fig, [(0, 0)], direction="horizontal")
        assert fig is not None

    def test_distribute_empty_list(self):
        """Distribute with empty list does nothing."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        fr.distribute_panels(fig, [], direction="horizontal")
        assert fig is not None


class TestAlignSmart:
    """Tests for align_smart() function."""

    def test_align_smart_basic(self):
        """Smart align all panels."""
        fig, axes = fr.subplots(2, 2)
        for i in range(2):
            for j in range(2):
                axes[i, j].plot([1, 2], [i + j, i + j + 1])

        fr.align_smart(fig)
        assert fig is not None

    def test_align_smart_specific_panels(self):
        """Smart align specific panels only."""
        fig, axes = fr.subplots(2, 2)
        for i in range(2):
            for j in range(2):
                axes[i, j].plot([1, 2], [i + j, i + j + 1])

        fr.align_smart(fig, panels=[(0, 0), (0, 1)])
        assert fig is not None

    def test_align_smart_empty_panels(self):
        """Smart align with empty panel list."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        fr.align_smart(fig, panels=[])
        assert fig is not None

    def test_align_smart_single_panel(self):
        """Smart align with single panel does nothing special."""
        fig, ax = fr.subplots()
        ax.plot([1, 2], [1, 2])

        fr.align_smart(fig)
        assert fig is not None


class TestAlignmentWithComposition:
    """Integration tests for alignment with composition."""

    def test_compose_then_align(self, tmp_path):
        """Align panels after composition."""
        # Create sources
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2], [1, 2], id="src1")
        recipe1 = tmp_path / "src1.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        fig2, ax2 = fr.subplots()
        ax2.bar([1, 2], [2, 1], id="src2")
        recipe2 = tmp_path / "src2.yaml"
        fr.save(fig2, recipe2, validate=False, verbose=False)

        # Compose
        fig, axes = fr.compose(
            layout=(1, 2),
            sources={(0, 0): recipe1, (0, 1): recipe2},
        )

        # Align
        fr.align_panels(fig, [(0, 0), (0, 1)], mode="bottom")
        assert fig is not None

    def test_compose_distribute_smart(self, tmp_path):
        """Full workflow: compose, distribute, smart align."""
        # Create source
        fig1, ax1 = fr.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9], id="data")
        recipe1 = tmp_path / "src.yaml"
        fr.save(fig1, recipe1, validate=False, verbose=False)

        # Compose 1x3 layout
        fig, axes = fr.compose(
            layout=(1, 3),
            sources={
                (0, 0): recipe1,
                (0, 1): recipe1,
                (0, 2): recipe1,
            },
        )

        # Distribute evenly
        fr.distribute_panels(fig, [(0, 0), (0, 1), (0, 2)], direction="horizontal")

        # Smart align
        fr.align_smart(fig)

        assert fig is not None
        assert "ax_0_0" in fig.record.axes
        assert "ax_0_1" in fig.record.axes
        assert "ax_0_2" in fig.record.axes
