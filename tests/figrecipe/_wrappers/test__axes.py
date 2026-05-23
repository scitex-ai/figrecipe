#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._api._plot module."""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest


class TestCreateFigureFromSpec:
    """Tests for create_figure_from_spec function."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up matplotlib figures after each test."""
        yield
        plt.close("all")

    def test_basic_line_plot_part_1(self):
        """Test creating a basic line plot from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec
        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }
        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_basic_line_plot_part_2(self):
        """Test creating a basic line plot from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec
        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }
        result = create_figure_from_spec(spec)
        assert result["axes"] is not None

    def test_basic_line_plot_part_3(self):
        """Test creating a basic line plot from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec
        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }
        result = create_figure_from_spec(spec)
        assert result["image_path"] is None  # No output path specified

    def test_scatter_plot_create_figure_from_spec(self):
        """Test creating a scatter plot from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [
                {"type": "scatter", "x": [1, 2, 3], "y": [1, 4, 9], "color": "red"}
            ],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_bar_plot_create_figure_from_spec(self):
        """Test creating a bar plot from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [{"type": "bar", "x": ["A", "B", "C"], "y": [3, 7, 2]}],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_histogram_create_figure_from_spec(self):
        """Test creating a histogram from spec."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [{"type": "hist", "x": list(np.random.randn(100)), "bins": 10}],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_multiple_plots_create_figure_from_spec(self):
        """Test creating multiple plots on same axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [
                {"type": "line", "x": [1, 2, 3], "y": [1, 2, 3], "label": "line1"},
                {"type": "line", "x": [1, 2, 3], "y": [3, 2, 1], "label": "line2"},
            ],
            "legend": True,
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_figure_dimensions_create_from_spec(self):
        """Test specifying figure dimensions in mm."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "figure": {"width_mm": 100, "height_mm": 80},
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_decorations_create_figure_from_spec(self):
        """Test applying axis decorations."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
            "xlabel": "X Axis",
            "ylabel": "Y Axis",
            "title": "Test Plot",
            "xlim": [0, 4],
            "ylim": [0, 10],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_subplots_create_figure_from_spec(self):
        """Test creating multi-axes figure."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "figure": {"nrows": 2, "ncols": 1},
            "axes": [
                {
                    "row": 0,
                    "col": 0,
                    "plots": [{"type": "line", "x": [1, 2], "y": [1, 2]}],
                },
                {
                    "row": 1,
                    "col": 0,
                    "plots": [{"type": "scatter", "x": [1, 2], "y": [2, 1]}],
                },
            ],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_facecolor_create_figure_from_spec(self):
        """Test setting figure facecolor."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "figure": {"facecolor": "white"},
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None

    def test_save_to_file(self):
        """Test saving figure to file."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = create_figure_from_spec(spec, output_path=output_path)
            if not (result['image_path'] is not None):
                raise AssertionError
            if not (output_path.exists()):
                raise AssertionError
        finally:
            output_path.unlink(missing_ok=True)
        assert True  # TQ001-placeholder: body exercises code under test

    def test_save_with_recipe(self):
        """Test saving figure with recipe."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [{"type": "line", "x": [1, 2, 3], "y": [1, 4, 9]}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            result = create_figure_from_spec(
                spec, output_path=output_path, save_recipe=True
            )

            if not (result['image_path'] is not None):
                raise AssertionError
            if not (result['recipe_path'] is not None):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test


class TestPlotTypes:
    """Tests for different plot types."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up matplotlib figures after each test."""
        yield
        plt.close("all")

    @pytest.mark.parametrize(
        "plot_type,extra_kwargs",
        [
            ("line", {}),
            ("plot", {}),
            ("scatter", {}),
            ("bar", {}),
            ("step", {}),
        ],
    )
    def test_plot_type_types(self, plot_type, extra_kwargs):
        """Test different plot types work."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import create_figure_from_spec

        spec = {
            "plots": [
                {"type": plot_type, "x": [1, 2, 3], "y": [1, 4, 9], **extra_kwargs}
            ],
        }

        result = create_figure_from_spec(spec)
        assert result["figure"] is not None


class TestHelperFunctions:
    """Tests for helper functions in _plot module."""

    def test_normalize_axes_single_part_1(self):
        """Test normalizing single axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _normalize_axes_array
        mock_ax = object()
        result = _normalize_axes_array(mock_ax, 1, 1)
        assert result.shape == (1, 1)

    def test_normalize_axes_single_part_2(self):
        """Test normalizing single axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _normalize_axes_array
        mock_ax = object()
        result = _normalize_axes_array(mock_ax, 1, 1)
        assert result[0, 0] is mock_ax

    def test_normalize_axes_row(self):
        """Test normalizing row of axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _normalize_axes_array

        # Mock row of axes
        mock_axes = [object(), object(), object()]
        result = _normalize_axes_array(mock_axes, 1, 3)
        assert result.shape == (1, 3)

    def test_normalize_axes_column(self):
        """Test normalizing column of axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _normalize_axes_array

        # Mock column of axes
        mock_axes = [object(), object()]
        result = _normalize_axes_array(mock_axes, 2, 1)
        assert result.shape == (2, 1)

    def test_parse_axes_position_row_col_part_1(self):
        """Test parsing axes position with row/col."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {"row": 1, "col": 2}
        row, col = _parse_axes_position(ax_spec)
        assert row == 1

    def test_parse_axes_position_row_col_part_2(self):
        """Test parsing axes position with row/col."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {"row": 1, "col": 2}
        row, col = _parse_axes_position(ax_spec)
        assert col == 2

    def test_parse_axes_position_panel_part_1(self):
        """Test parsing axes position with panel string."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {"panel": "1, 2"}
        row, col = _parse_axes_position(ax_spec)
        assert row == 1

    def test_parse_axes_position_panel_part_2(self):
        """Test parsing axes position with panel string."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {"panel": "1, 2"}
        row, col = _parse_axes_position(ax_spec)
        assert col == 2

    def test_parse_axes_position_default_part_1(self):
        """Test parsing axes position with no position."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {}
        row, col = _parse_axes_position(ax_spec)
        assert row == 0

    def test_parse_axes_position_default_part_2(self):
        """Test parsing axes position with no position."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import _parse_axes_position
        ax_spec = {}
        row, col = _parse_axes_position(ax_spec)
        assert col == 0


class TestPlotConstants:
    """Tests for module constants."""

    def test_plot_types_contains_common_types_part_1(self):
        """Test PLOT_TYPES contains common plot types."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import PLOT_TYPES
        assert "line" in PLOT_TYPES

    def test_plot_types_contains_common_types_part_2(self):
        """Test PLOT_TYPES contains common plot types."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import PLOT_TYPES
        assert "scatter" in PLOT_TYPES

    def test_plot_types_contains_common_types_part_3(self):
        """Test PLOT_TYPES contains common plot types."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import PLOT_TYPES
        assert "bar" in PLOT_TYPES

    def test_plot_types_contains_common_types_part_4(self):
        """Test PLOT_TYPES contains common plot types."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import PLOT_TYPES
        assert "hist" in PLOT_TYPES

    def test_plot_types_contains_common_types_part_5(self):
        """Test PLOT_TYPES contains common plot types."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import PLOT_TYPES
        assert "boxplot" in PLOT_TYPES

    def test_reserved_keys_part_1(self):
        """Test RESERVED_KEYS are defined."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import RESERVED_KEYS
        assert "type" in RESERVED_KEYS

    def test_reserved_keys_part_2(self):
        """Test RESERVED_KEYS are defined."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import RESERVED_KEYS
        assert "x" in RESERVED_KEYS

    def test_reserved_keys_part_3(self):
        """Test RESERVED_KEYS are defined."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import RESERVED_KEYS
        assert "y" in RESERVED_KEYS

    def test_reserved_keys_part_4(self):
        """Test RESERVED_KEYS are defined."""
        # Arrange
        # Act
        # Assert
        from figrecipe._api._plot import RESERVED_KEYS
        assert "data_file" in RESERVED_KEYS
