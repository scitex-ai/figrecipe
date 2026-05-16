#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for annotation fontsize styling (Issue #43).

Tests that ax.text() and ax.annotate() use the style's annotation_pt
as the default fontsize when no fontsize is specified.
"""

import pytest


@pytest.fixture
def fig_ax_with_scitex():
    """Create figure and axes with SCITEX style loaded."""
    import figrecipe as fr

    fr.load_style("SCITEX")
    fig, ax = fr.subplots()
    yield fig, ax
    import matplotlib.pyplot as plt

    plt.close(fig.fig)


class TestTextAnnotationFontsize:
    """Tests for ax.text() annotation_pt default."""

    def test_text_uses_scitex_annotation_pt(self, fig_ax_with_scitex):
        """ax.text() should use annotation_pt (6pt) from SCITEX style."""
        fig, ax = fig_ax_with_scitex
        text_obj = ax.text(0.5, 0.5, "Test annotation")

        # SCITEX defines annotation_pt: 6
        assert text_obj.get_fontsize() == 6

    def test_text_override_fontsize(self, fig_ax_with_scitex):
        """Explicit fontsize should override style default."""
        fig, ax = fig_ax_with_scitex
        text_obj = ax.text(0.5, 0.5, "Test annotation", fontsize=12)

        assert text_obj.get_fontsize() == 12


class TestAnnotateAnnotationFontsize:
    """Tests for ax.annotate() annotation_pt default."""

    def test_annotate_uses_scitex_annotation_pt(self, fig_ax_with_scitex):
        """ax.annotate() should use annotation_pt (6pt) from SCITEX style."""
        fig, ax = fig_ax_with_scitex
        annot_obj = ax.annotate("Test", xy=(0.5, 0.5))

        # SCITEX defines annotation_pt: 6
        assert annot_obj.get_fontsize() == 6

    def test_annotate_override_fontsize(self, fig_ax_with_scitex):
        """Explicit fontsize should override style default."""
        fig, ax = fig_ax_with_scitex
        annot_obj = ax.annotate("Test", xy=(0.5, 0.5), fontsize=10)

        assert annot_obj.get_fontsize() == 10

    def test_annotate_with_xytext(self, fig_ax_with_scitex):
        """ax.annotate() with xytext should still use annotation_pt."""
        fig, ax = fig_ax_with_scitex
        annot_obj = ax.annotate(
            "Test", xy=(0.5, 0.5), xytext=(0.7, 0.7), arrowprops=dict(arrowstyle="->")
        )

        assert annot_obj.get_fontsize() == 6


class TestTextRecording:
    """Tests that text calls are properly recorded for reproduction."""

    def test_text_is_recorded(self, fig_ax_with_scitex, tmp_path):
        """ax.text() calls should be recorded in the recipe."""
        import figrecipe as fr

        fig, ax = fig_ax_with_scitex
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.text(0.05, 0.95, "r = 0.99", transform=ax.transAxes)

        # Save and check the recipe contains the text call
        output_path = tmp_path / "test.png"
        fr.save(fig, output_path, validate=False, verbose=False)

        # Check that the decoration (text) is recorded
        ax_record = fig.record.get_or_create_axes(0, 0)
        assert len(ax_record.decorations) > 0

        # Find the text call
        text_calls = [d for d in ax_record.decorations if d.function == "text"]
        assert len(text_calls) == 1
        assert "fontsize" in text_calls[0].kwargs
        assert text_calls[0].kwargs["fontsize"] == 6

    def test_annotate_is_recorded(self, fig_ax_with_scitex, tmp_path):
        """ax.annotate() calls should be recorded in the recipe."""
        import figrecipe as fr

        fig, ax = fig_ax_with_scitex
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.annotate("Peak", xy=(2, 2))

        # Save and check the recipe contains the annotate call
        output_path = tmp_path / "test.png"
        fr.save(fig, output_path, validate=False, verbose=False)

        # Check that the decoration (annotate) is recorded
        ax_record = fig.record.get_or_create_axes(0, 0)
        annotate_calls = [d for d in ax_record.decorations if d.function == "annotate"]
        assert len(annotate_calls) == 1
        assert "fontsize" in annotate_calls[0].kwargs
        assert annotate_calls[0].kwargs["fontsize"] == 6
