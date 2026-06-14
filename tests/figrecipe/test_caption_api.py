#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the figrecipe caption API (fr.compose, fr.subplots, add_figure_caption)."""

import matplotlib.pyplot as _plt
import pytest


class TestSubplotsCaption:
    """Test fr.subplots(caption=...) works."""

    def test_subplots_no_caption_returns_fig(self):
        import figrecipe as fr

        fig, axes = fr.subplots()
        assert fig is not None
        assert axes is not None
        _plt.close(fig)

    def test_subplots_with_caption(self):
        import figrecipe as fr

        fig, axes = fr.subplots(caption="Test caption text")
        assert fig.record.caption == "Test caption text"
        _plt.close(fig)

    def test_subplots_caption_persists_on_record(self):
        import figrecipe as fr

        fig, axes = fr.subplots(caption="Persist me")
        assert fig.record.caption == "Persist me"
        # Also verify the caption is stored in figure_texts
        assert len(fig.record.figure_texts) > 0
        _plt.close(fig)

    def test_subplots_caption_none_omitted(self):
        import figrecipe as fr

        fig, axes = fr.subplots(caption=None)
        # No exception should be raised
        _plt.close(fig)


class TestComposeCaption:
    """Test fr.compose(caption=..., panel_captions=...)."""

    def test_compose_with_figure_caption(self):
        """Composing with a figure-level caption works."""
        import figrecipe as fr

        # Minimal source: one fr.subplots axis with a single ided plot, saved as recipe.
        fig_base, ax_base = fr.subplots()
        ax_base.plot([1, 2, 3], [1, 4, 9], id="line1")
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = os.path.join(tmpdir, "src.yaml")
            fr.save(fig_base, src_path, validate=False, verbose=False)
            _plt.close(fig_base)

            fig, axes = fr.compose(
                layout=(1, 1),
                sources={(0, 0): src_path},
                caption="Composed figure caption",
            )
            assert fig.record.caption == "Composed figure caption"
            _plt.close(fig)

    def test_compose_with_panel_captions(self):
        """Composing with panel captions stores them."""
        import figrecipe as fr

        # Minimal source: one fr.subplots axis with a single ided plot, saved as recipe.
        fig_base, ax_base = fr.subplots()
        ax_base.plot([1, 2, 3], [1, 4, 9], id="line1")
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = os.path.join(tmpdir, "src.yaml")
            # Save a minimal recipe
            fr.save(fig_base, src_path, validate=False, verbose=False)
            _plt.close(fig_base)

            fig, axes = fr.compose(
                layout=(1, 2),
                sources={
                    (0, 0): src_path,
                    (0, 1): src_path,
                },
                caption="Panel caption figure",
                panel_captions=["Panel A", "Panel B"],
            )
            assert fig.record.caption == "Panel caption figure"
            assert fig.record.figure_panel_captions == ["Panel A", "Panel B"]
            _plt.close(fig)


class TestPublicCaptionAPI:
    """Test public caption API functions."""

    def test_add_figure_caption_exists(self):
        import figrecipe as fr

        assert hasattr(fr, "add_figure_caption")
        assert callable(fr.add_figure_caption)

    def test_add_panel_captions_exists(self):
        import figrecipe as fr

        assert hasattr(fr, "add_panel_captions")
        assert callable(fr.add_panel_captions)

    def test_panel_label_exists(self):
        import figrecipe as fr

        assert hasattr(fr, "panel_label")
        assert callable(fr.panel_label)

    def test_add_figure_caption_strips_markdown(self):
        """add_figure_caption should strip Markdown bold/italic markers."""
        import figrecipe as fr

        fig, ax = _plt.subplots()
        result = fr.add_figure_caption(fig, "**Bold** and *italic*")
        assert "**" not in result
        assert "*" not in result
        _plt.close(fig)

    def test_panel_label_on_recording_axes(self):
        """panel_label should work on RecordingAxes."""
        import figrecipe as fr

        fig, axes = fr.subplots()
        ax = axes if hasattr(axes, "text") else axes[0]
        # Should not raise
        fr.panel_label(ax, "A")
        _plt.close(fig)


class TestFigureRecordRoundTrip:
    """Test caption persistence in FigureRecord serialization."""

    def test_figure_panel_captions_in_to_dict(self):
        from figrecipe._recorder import FigureRecord

        record = FigureRecord()
        record.figure_panel_captions = ["A caption", "B caption"]
        d = record.to_dict()
        assert d["figure"]["panel_captions"] == ["A caption", "B caption"]

    def test_figure_panel_captions_from_dict(self):
        from figrecipe._recorder import FigureRecord

        d = {"figure": {"panel_captions": ["capt1", "capt2"]}}
        record = FigureRecord.from_dict(d)
        assert record.figure_panel_captions == ["capt1", "capt2"]
