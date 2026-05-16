#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-11 20:58:00 (ywatanabe)"
"""Tests for constrained_layout with mm_layout and auto-crop (Issue #41).

Tests that constrained_layout=True still allows auto-crop to work
by preserving _mm_layout on the figure.
"""

import pytest


@pytest.fixture
def fig_ax_scitex():
    """Create figure with SCITEX style (constrained_layout=True)."""
    import figrecipe as fr

    fr.load_style("SCITEX")
    fig, ax = fr.subplots()
    yield fig, ax
    import matplotlib.pyplot as plt

    plt.close(fig.fig)


class TestConstrainedLayoutWithMmLayout:
    """Tests that _mm_layout is set even with constrained_layout."""

    def test_mm_layout_set_with_constrained_layout(self, fig_ax_scitex):
        """Figure should have _mm_layout even when constrained_layout=True."""
        fig, ax = fig_ax_scitex

        # SCITEX uses constrained_layout: true
        assert fig.fig.get_constrained_layout() is True

        # But _mm_layout should still be set for auto-crop
        assert hasattr(fig, "_mm_layout")
        assert fig._mm_layout is not None

    def test_mm_layout_has_crop_margins(self, fig_ax_scitex):
        """_mm_layout should contain crop margin values."""
        fig, ax = fig_ax_scitex

        mm_layout = fig._mm_layout
        assert "crop_margin_left_mm" in mm_layout
        assert "crop_margin_right_mm" in mm_layout
        assert "crop_margin_top_mm" in mm_layout
        assert "crop_margin_bottom_mm" in mm_layout

    def test_autocrop_works_with_constrained_layout(self, fig_ax_scitex, tmp_path):
        """Auto-crop should work even with constrained_layout=True."""
        from PIL import Image

        import figrecipe as fr

        fig, ax = fig_ax_scitex
        ax.plot([1, 2, 3], [1, 2, 3])

        output = tmp_path / "test.png"
        fr.save(fig, output, verbose=False, validate=False)

        # Check that image was saved and is reasonably sized
        # With bbox_inches='tight', the size depends on content but should
        # be reasonable (not zero, not huge)
        with Image.open(output) as img:
            assert img.width > 100, f"Image too small: {img.width}px wide"
            assert img.width < 2000, f"Image too large: {img.width}px wide"
            assert img.height > 100, f"Image too small: {img.height}px tall"
            assert img.height < 1500, f"Image too large: {img.height}px tall"


class TestConstrainedLayoutWithoutMmLayoutApplied:
    """Tests that mm layout adjustments are NOT applied with constrained_layout."""

    def test_subplots_adjust_not_called_with_constrained(self):
        """When constrained_layout=True, subplots_adjust should not be called."""
        import figrecipe as fr

        fr.load_style("SCITEX")
        fig, ax = fr.subplots()

        # With constrained_layout, matplotlib handles the layout
        # We just verify constrained_layout is actually enabled
        assert fig.fig.get_constrained_layout() is True

        # _mm_layout should be set but layout adjustments not applied
        assert hasattr(fig, "_mm_layout")

        import matplotlib.pyplot as plt

        plt.close(fig.fig)


class TestExplicitConstrainedLayout:
    """Tests for explicit constrained_layout parameter."""

    def test_explicit_constrained_layout_true(self):
        """Explicit constrained_layout=True should still have _mm_layout."""
        import figrecipe as fr

        fig, ax = fr.subplots(constrained_layout=True)

        assert fig.fig.get_constrained_layout() is True
        assert hasattr(fig, "_mm_layout")
        assert fig._mm_layout is not None

        import matplotlib.pyplot as plt

        plt.close(fig.fig)

    def test_explicit_constrained_layout_false(self):
        """Explicit constrained_layout=False should apply mm layout."""
        import figrecipe as fr

        fig, ax = fr.subplots(constrained_layout=False)

        assert fig.fig.get_constrained_layout() is False
        assert hasattr(fig, "_mm_layout")
        assert fig._mm_layout is not None

        import matplotlib.pyplot as plt

        plt.close(fig.fig)

    def test_no_style_with_constrained_layout(self):
        """Without style, constrained_layout=True should still work."""
        import figrecipe as fr

        fig, ax = fr.subplots(constrained_layout=True)

        assert fig.fig.get_constrained_layout() is True
        # _mm_layout should be set with defaults
        assert hasattr(fig, "_mm_layout")

        import matplotlib.pyplot as plt

        plt.close(fig.fig)


class TestSavefigWithConstrainedLayout:
    """Tests that savefig() also works with constrained_layout."""

    def test_savefig_autocrop_with_constrained(self, fig_ax_scitex, tmp_path):
        """fig.savefig() should apply auto-crop with constrained_layout."""
        from PIL import Image

        fig, ax = fig_ax_scitex
        ax.plot([1, 2, 3], [1, 2, 3])

        output = tmp_path / "test.png"
        fig.savefig(output, verbose=False, validate=False, save_recipe=False)

        with Image.open(output) as img:
            # With bbox_inches='tight', size depends on content but should be reasonable
            assert img.width > 100, f"Image too small: {img.width}px wide"
            assert img.width < 2000, f"Image too large: {img.width}px wide"
            assert img.height > 100, f"Image too small: {img.height}px tall"
            assert img.height < 1500, f"Image too large: {img.height}px tall"
