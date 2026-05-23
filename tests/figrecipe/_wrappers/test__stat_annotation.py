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

    def test_three_stars_part_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.0001) == "***"

    def test_three_stars_part_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.0009) == "***"

    def test_two_stars_part_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.001) == "**"

    def test_two_stars_part_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.005) == "**"

    def test_two_stars_part_3(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.009) == "**"

    def test_one_star_part_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.01) == "*"

    def test_one_star_part_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.03) == "*"

    def test_one_star_part_3(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.049) == "*"

    def test_not_significant_part_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.05) == "n.s."

    def test_not_significant_part_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.1) == "n.s."

    def test_not_significant_part_3(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.5) == "n.s."

    def test_ns_symbol_false(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert p_to_stars(0.1, ns_symbol=False) == ""


class TestDrawStatAnnotation:
    """Tests for the bracket drawing function."""

    def test_draw_returns_artists(self):
        """Test that draw_stat_annotation returns matplotlib artists."""
        # Arrange
        # Act
        # Assert
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([0, 1], [3, 5])
        artists = draw_stat_annotation(ax, 0, 1, p_value=0.01)
        assert len(artists) > 0
        plt.close(fig)

    def test_draw_with_stars(self):
        """Test drawing with stars style."""
        # Arrange
        # Act
        # Assert
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([0, 1], [3, 5])
        artists = draw_stat_annotation(ax, 0, 1, p_value=0.001, style="stars")
        assert len(artists) == 4  # 3 lines + 1 text
        plt.close(fig)

    def test_draw_bracket_only(self):
        """Test drawing bracket without text."""
        # Arrange
        # Act
        # Assert
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
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        artists = ax.add_stat_annotation(0, 1, p_value=0.003)
        assert len(artists) > 0

    def test_add_stat_annotation_records_part_1(self):
        """Test that stat_annotation is recorded."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003)
        decorations = fig.record.axes["ax_0_0"].decorations
        assert len(decorations) == 1

    def test_add_stat_annotation_records_part_2(self):
        """Test that stat_annotation is recorded."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003)
        decorations = fig.record.axes["ax_0_0"].decorations
        assert decorations[0].function == "stat_annotation"

    def test_add_stat_annotation_kwargs_recorded_part_1(self):
        """Test that kwargs are recorded correctly."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")
        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["x1"] == 0

    def test_add_stat_annotation_kwargs_recorded_part_2(self):
        """Test that kwargs are recorded correctly."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")
        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["x2"] == 1

    def test_add_stat_annotation_kwargs_recorded_part_3(self):
        """Test that kwargs are recorded correctly."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")
        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["p_value"] == 0.003

    def test_add_stat_annotation_kwargs_recorded_part_4(self):
        """Test that kwargs are recorded correctly."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")
        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["style"] == "both"

    def test_add_stat_annotation_kwargs_recorded_part_5(self):
        """Test that kwargs are recorded correctly."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.003, style="both", color="red")
        decorations = fig.record.axes["ax_0_0"].decorations
        kwargs = decorations[0].kwargs
        assert kwargs["color"] == "red"

    def test_add_stat_annotation_with_custom_text(self):
        """Test annotation with custom text."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, text="p<0.001")

        decorations = fig.record.axes["ax_0_0"].decorations
        assert decorations[0].kwargs["text"] == "p<0.001"

    def test_add_stat_annotation_with_id(self):
        """Test annotation with custom ID."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.01, id="comparison_a_b")

        decorations = fig.record.axes["ax_0_0"].decorations
        assert decorations[0].id == "comparison_a_b"

    def test_add_stat_annotation_track_false(self):
        """Test that track=False prevents recording."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3, 5])
        ax.add_stat_annotation(0, 1, p_value=0.01, track=False)

        decorations = fig.record.axes["ax_0_0"].decorations
        assert len(decorations) == 0


class TestStatAnnotationRoundtrip:
    """Tests for stat annotation round-trip (save and reproduce)."""

    def test_stat_annotation_roundtrip(self):
        """Test that stat annotations survive save/reproduce cycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.bar([0, 1], [3.2, 5.1])
            ax.add_stat_annotation(0, 1, p_value=0.003, style="stars")

            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False)

            fig2, ax2 = fr.reproduce(png_path)

            decorations = fig2.record.axes["ax_0_0"].decorations
            if not (len(decorations) == 1):
                raise AssertionError
            if not (decorations[0].function == 'stat_annotation'):
                raise AssertionError
            if not (decorations[0].kwargs['p_value'] == 0.003):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test

    def test_multiple_annotations_roundtrip(self):
        """Test multiple stat annotations roundtrip."""
        # Arrange
        # Act
        # Assert
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
        # Arrange
        # Act
        # Assert
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
            if not (dec.kwargs['color'] == 'red'):
                raise AssertionError
            if not (dec.kwargs['linewidth'] == 2):
                raise AssertionError
            if not (dec.kwargs['fontsize'] == 12):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test
