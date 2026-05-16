#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for caption generation features."""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._wrappers._caption_generator import (
    format_comparison,
    format_panel_stats,
    format_stats_value,
    generate_figure_caption,
    generate_panel_caption,
)


class TestFormatStatsValue:
    """Tests for statistics value formatting."""

    def test_normal_value(self):
        assert format_stats_value(3.14159) == "3.14"

    def test_large_value(self):
        assert "e" in format_stats_value(10000)

    def test_small_value(self):
        assert "e" in format_stats_value(0.001)

    def test_zero(self):
        assert format_stats_value(0) == "0.00"


class TestFormatComparison:
    """Tests for comparison formatting."""

    def test_publication_style(self):
        comp = {"name": "A vs B", "p_value": 0.003}
        result = format_comparison(comp, style="publication")
        assert "A vs B" in result
        assert "p=" in result or "p<" in result

    def test_brief_style(self):
        comp = {"name": "A vs B", "p_value": 0.001}
        result = format_comparison(comp, style="brief")
        assert "A vs B" in result
        assert "**" in result  # Two stars for p=0.001

    def test_detailed_style(self):
        comp = {"name": "A vs B", "p_value": 0.01, "method": "t-test"}
        result = format_comparison(comp, style="detailed")
        assert "A vs B" in result
        assert "t-test" in result

    def test_with_effect_size(self):
        comp = {"name": "A vs B", "p_value": 0.01, "effect_size": 0.8}
        result = format_comparison(comp, style="publication")
        assert "d=0.80" in result

    def test_with_effect_size_dict(self):
        comp = {
            "name": "A vs B",
            "p_value": 0.01,
            "effect_size": {"name": "r", "value": 0.5},
        }
        result = format_comparison(comp, style="detailed")
        assert "r=0.50" in result


class TestFormatPanelStats:
    """Tests for panel stats formatting."""

    def test_with_n(self):
        stats = {"n": 50}
        result = format_panel_stats(stats)
        assert "n=50" in result

    def test_with_mean_std(self):
        stats = {"mean": 3.2, "std": 1.1}
        result = format_panel_stats(stats)
        assert "mean=" in result
        assert "±" in result

    def test_with_sem(self):
        stats = {"mean": 3.2, "sem": 0.15}
        result = format_panel_stats(stats)
        assert "SEM" in result

    def test_with_group(self):
        stats = {"group": "Control", "n": 25}
        result = format_panel_stats(stats)
        assert "Control" in result


class TestGenerateFigureCaption:
    """Tests for figure caption generation."""

    def test_with_title_only(self):
        caption = generate_figure_caption(title="Effect of treatment")
        assert "Effect of treatment." in caption

    def test_with_panels(self):
        caption = generate_figure_caption(
            title="Multi-panel figure", panel_captions=["(A) Control", "(B) Treatment"]
        )
        assert "(A) Control" in caption
        assert "(B) Treatment" in caption

    def test_with_stats(self):
        stats = {"comparisons": [{"name": "Control vs Treatment", "p_value": 0.003}]}
        caption = generate_figure_caption(title="Results", stats=stats)
        assert "Control vs Treatment" in caption

    def test_custom_template(self):
        caption = generate_figure_caption(
            title="My Title", panel_captions=["Panel A"], template="{title} - {panels}"
        )
        assert "My Title - Panel A" in caption

    def test_brief_style(self):
        stats = {"comparisons": [{"name": "A vs B", "p_value": 0.0001}]}
        caption = generate_figure_caption(stats=stats, style="brief")
        assert "***" in caption  # Three stars for p<0.001


class TestGeneratePanelCaption:
    """Tests for panel caption generation."""

    def test_with_label(self):
        caption = generate_panel_caption(label="A")
        assert "(A)" in caption

    def test_with_stats(self):
        stats = {"n": 50, "mean": 3.2, "std": 1.1}
        caption = generate_panel_caption(label="A", stats=stats)
        assert "(A)" in caption
        assert "n=50" in caption

    def test_label_already_parenthesized(self):
        caption = generate_panel_caption(label="(A)")
        assert caption.count("(A)") == 1  # Not double-wrapped


class TestRecordingFigureGenerateCaption:
    """Tests for RecordingFigure.generate_caption()."""

    def test_basic_caption(self):
        fig, ax = fr.subplots()
        fig.set_title_metadata("Test Figure")
        caption = fig.generate_caption()
        assert "Test Figure." in caption

    def test_caption_with_stats(self):
        fig, ax = fr.subplots()
        fig.set_title_metadata("Statistical Results")
        fig.set_stats({"comparisons": [{"name": "Group A vs B", "p_value": 0.01}]})
        caption = fig.generate_caption()
        assert "Group A vs B" in caption

    def test_caption_with_panels(self):
        fig, axes = fr.subplots(1, 2)
        fig.set_title_metadata("Multi-panel")
        axes[0].set_caption("(A) First panel")
        axes[1].set_caption("(B) Second panel")
        caption = fig.generate_caption()
        assert "(A) First panel" in caption
        assert "(B) Second panel" in caption


class TestRecordingAxesGeneratePanelCaption:
    """Tests for RecordingAxes.generate_panel_caption()."""

    def test_basic_panel_caption(self):
        fig, ax = fr.subplots()
        ax.set_stats({"n": 30, "mean": 5.5})
        caption = ax.generate_panel_caption(label="A")
        assert "(A)" in caption
        assert "n=30" in caption

    def test_panel_caption_without_label(self):
        fig, ax = fr.subplots()
        ax.set_stats({"n": 30})
        caption = ax.generate_panel_caption()
        assert "n=30" in caption

    def test_panel_caption_styles(self):
        fig, ax = fr.subplots()
        ax.set_stats({"n": 30, "mean": 5.5, "std": 1.2})

        pub_caption = ax.generate_panel_caption(style="publication")
        brief_caption = ax.generate_panel_caption(style="brief")
        detailed_caption = ax.generate_panel_caption(style="detailed")

        # All should contain the basic stats
        assert "n=30" in pub_caption
        assert "n=30" in brief_caption
        assert "n=30" in detailed_caption
