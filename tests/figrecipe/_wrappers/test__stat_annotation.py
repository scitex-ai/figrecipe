#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for statistical annotation features (brackets and stars)."""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._wrappers._stat_annotation import draw_stat_annotation, p_to_stars


class TestPToStars:
    """Tests for p-value to stars conversion."""

    def test_three_stars(self):
        assert p_to_stars(0.0001) == "***"
        assert p_to_stars(0.0009) == "***"

    def test_two_stars(self):
        assert p_to_stars(0.001) == "**"
        assert p_to_stars(0.005) == "**"
        assert p_to_stars(0.009) == "**"

    def test_one_star(self):
        assert p_to_stars(0.01) == "*"
        assert p_to_stars(0.03) == "*"
        assert p_to_stars(0.049) == "*"

    def test_not_significant(self):
        assert p_to_stars(0.05) == "n.s."
        assert p_to_stars(0.1) == "n.s."
        assert p_to_stars(0.5) == "n.s."

    def test_ns_symbol_false(self):
        assert p_to_stars(0.1, ns_symbol=False) == ""


class TestDrawStatAnnotation:
    """Tests for the bracket drawing function."""

    def test_draw_returns_artists(self):
        """Test that draw_stat_annotation returns matplotlib artists."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([0, 1], [3, 5])
        artists = draw_stat_annotation(ax, 0, 1, p_value=0.01)
        assert len(artists) > 0
        plt.close(fig)

    def test_draw_with_stars(self):
        """Test drawing with stars style."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([0, 1], [3, 5])
        artists = draw_stat_annotation(ax, 0, 1, p_value=0.001, style="stars")
        assert len(artists) == 4  # 3 lines + 1 text
        plt.close(fig)

    def test_draw_bracket_only(self):
        """Test drawing bracket without text."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([0, 1], [3, 5])
        artists = draw_stat_annotation(ax, 0, 1, style="bracket_only")
        assert len(artists) == 3  # 3 lines only
        plt.close(fig)


class TestAddStatAnnotation:
    """Tests for RecordingAxes.add_stat_annotation()."""

    def test_add_stat_annotation_returns_artists(self):
        """Test that add_stat_annotation returns artists."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        artists = ax.add_stat_annotation(0, 1, p_value=0.003)
        assert len(artists) > 0

    def test_add_stat_annotation_records(self):
        """Test that stat_annotation is recorded."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003)

        decorations = fig.record.axes["ax_0_0"].decorations
        assert len(decorations) == 1
        assert decorations[0].function == "stat_annotation"

    def test_add_stat_annotation_kwargs_recorded(self):
        """Test that kwargs are recorded correctly."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")

        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["x1"] == 0
        assert kwargs["x2"] == 1
        assert kwargs["p_value"] == 0.003
        assert kwargs["style"] == "both"
        assert kwargs["color"] == "red"

    def test_add_stat_annotation_with_custom_text(self):
        """Test annotation with custom text."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, text="p<0.001")

        decorations = fig.record.axes["ax_0_0"].decorations
        assert decorations[0].kwargs["text"] == "p<0.001"

    def test_add_stat_annotation_with_id(self):
        """Test annotation with custom ID."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.01, id="comparison_a_b")

        decorations = fig.record.axes["ax_0_0"].decorations
        assert decorations[0].id == "comparison_a_b"

    def test_add_stat_annotation_track_false(self):
        """Test that track=False prevents recording."""
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.01, track=False)

        decorations = fig.record.axes["ax_0_0"].decorations
        assert len(decorations) == 0


class TestStatAnnotationRoundtrip:
    """Tests for stat annotation round-trip (save and reproduce)."""

    def test_stat_annotation_roundtrip(self):
        """Test that stat annotations survive save/reproduce cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.bar([0, 1], [3.2, 5.1])
            ax.add_stat_annotation(0, 1, p_value=0.003, style="stars")

            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False)

            fig2, ax2 = fr.reproduce(png_path)

            decorations = fig2.record.axes["ax_0_0"].decorations
            assert len(decorations) == 1
            assert decorations[0].function == "stat_annotation"
            assert decorations[0].kwargs["p_value"] == 0.003

    def test_multiple_annotations_roundtrip(self):
        """Test multiple stat annotations roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.bar([0, 1, 2], [3.2, 5.1, 4.0])
            ax.add_stat_annotation(0, 1, p_value=0.003, y=6)
            ax.add_stat_annotation(1, 2, p_value=0.05, y=6.5)
            ax.add_stat_annotation(0, 2, p_value=0.001, y=7)

            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False, validate=False)

            fig2, ax2 = fr.reproduce(png_path)

            decorations = fig2.record.axes["ax_0_0"].decorations
            assert len(decorations) == 3

    def test_annotation_with_custom_styling_roundtrip(self):
        """Test annotation with custom styling roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.bar([0, 1], [3.2, 5.1])
            ax.add_stat_annotation(
                0, 1, p_value=0.01, style="both", color="red", linewidth=2, fontsize=12
            )

            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False)

            fig2, ax2 = fr.reproduce(png_path)

            dec = fig2.record.axes["ax_0_0"].decorations[0]
            assert dec.kwargs["color"] == "red"
            assert dec.kwargs["linewidth"] == 2
            assert dec.kwargs["fontsize"] == 12
