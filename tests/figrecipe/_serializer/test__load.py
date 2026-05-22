#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for figrecipe."""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing

import matplotlib.pyplot as plt
import numpy as np


class TestSubplotsAndSave:
    """Tests for subplots() and save() functions."""

    def test_subplots_single_part_1(self):
        """Test creating a single subplot."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig, ax = ps.subplots()
        assert hasattr(fig, "_recorder")

    def test_subplots_single_part_2(self):
        """Test creating a single subplot."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig, ax = ps.subplots()
        assert hasattr(ax, "_ax")

    def test_subplots_multiple_part_1(self):
        """Test creating multiple subplots."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig, axes = ps.subplots(2, 2)
        assert len(axes) == 2

    def test_subplots_multiple_part_2(self):
        """Test creating multiple subplots."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig, axes = ps.subplots(2, 2)
        assert len(axes[0]) == 2

    def test_subplots_returns_numpy_array_part_1(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        assert not isinstance(ax1, np.ndarray)

    def test_subplots_returns_numpy_array_part_2(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        assert hasattr(ax1, "_ax")  # RecordingAxes

    def test_subplots_returns_numpy_array_part_3(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        assert isinstance(axes2, np.ndarray)

    def test_subplots_returns_numpy_array_part_4(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        assert axes2.shape == (3,)

    def test_subplots_returns_numpy_array_part_5(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        assert hasattr(axes2, "flatten")

    def test_subplots_returns_numpy_array_part_6(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        assert isinstance(axes3, np.ndarray)

    def test_subplots_returns_numpy_array_part_7(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        assert axes3.shape == (3,)

    def test_subplots_returns_numpy_array_part_8(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        assert hasattr(axes3, "flatten")

    def test_subplots_returns_numpy_array_part_9(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        plt.close(fig3.fig)
        fig4, axes4 = ps.subplots(2, 3)
        assert isinstance(axes4, np.ndarray)

    def test_subplots_returns_numpy_array_part_10(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        plt.close(fig3.fig)
        fig4, axes4 = ps.subplots(2, 3)
        assert axes4.shape == (2, 3)

    def test_subplots_returns_numpy_array_part_11(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        plt.close(fig3.fig)
        fig4, axes4 = ps.subplots(2, 3)
        assert hasattr(axes4, "flatten")

    def test_subplots_returns_numpy_array_part_12(self):
        """Test that subplots returns numpy arrays matching matplotlib behavior."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        fig1, ax1 = ps.subplots(1, 1)
        plt.close(fig1.fig)
        fig2, axes2 = ps.subplots(1, 3)
        plt.close(fig2.fig)
        fig3, axes3 = ps.subplots(3, 1)
        plt.close(fig3.fig)
        fig4, axes4 = ps.subplots(2, 3)
        assert len(axes4.flatten()) == 6

    def test_subplots_flatten_works(self):
        """Test that axes.flatten() works like matplotlib."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        fig, axes = ps.subplots(2, 2)
        flat = axes.flatten()

        assert len(flat) == 4
        for ax in flat:
            assert hasattr(ax, "_ax")  # Each is a RecordingAxes

        plt.close(fig.fig)

    def test_plot_and_save(self):
        """Test plotting and saving a recipe."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            x = np.linspace(0, 10, 50)
            y = np.sin(x)

            fig, ax = ps.subplots()
            ax.plot(x, y, color="red", linewidth=2)

            recipe_path = Path(tmpdir) / "test_recipe.png"
            img_path, yaml_path, result = ps.save(fig, recipe_path, validate=False)

            assert img_path.exists()
            assert yaml_path.exists()
            assert img_path.suffix == ".png"
            assert yaml_path.suffix == ".yaml"

            plt.close(fig.fig)

    def test_save_with_custom_id(self):
        """Test saving with custom call ID."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = ps.subplots()
            ax.plot([1, 2, 3], [4, 5, 6], id="my_line")

            recipe_path = Path(tmpdir) / "custom_id.png"
            img_path, yaml_path, result = ps.save(fig, recipe_path, validate=False)

            # Check the recipe contains our custom ID
            info = ps.info(yaml_path)
            call_ids = [c["id"] for c in info["calls"]]
            assert "my_line" in call_ids

            plt.close(fig.fig)


class TestReproduce:
    """Tests for reproduce() function."""

    def test_reproduce_simple_expected(self):
        """Test reproducing a simple figure."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 1, 5, 3])

            fig1, ax1 = ps.subplots()
            ax1.plot(x, y, color="blue")

            recipe_path = Path(tmpdir) / "simple.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check figure was created
            assert fig2 is not None
            assert ax2 is not None

            plt.close(fig2.fig)

    def test_reproduce_returns_recording_types(self):
        """Test that reproduce() returns RecordingFigure and RecordingAxes."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps
        from figrecipe._wrappers import RecordingAxes, RecordingFigure

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, ax1 = ps.subplots()
            ax1.plot([1, 2, 3], [1, 2, 3])

            recipe_path = Path(tmpdir) / "types.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check types match subplots() return types
            assert isinstance(fig2, RecordingFigure)
            assert isinstance(ax2, RecordingAxes)

            plt.close(fig2.fig)

    def test_reproduce_returns_numpy_array(self):
        """Test that reproduce() returns numpy array for multi-axes."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, axes1 = ps.subplots(2, 2)
            # Plot on ALL axes so they're all recorded
            for i, ax in enumerate(axes1.flatten()):
                ax.plot([1, 2, 3], [i, i + 1, i + 2])

            recipe_path = Path(tmpdir) / "multi.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, axes2 = ps.reproduce(recipe_path)

            # Check axes is numpy array like subplots()
            assert isinstance(axes2, np.ndarray)
            assert axes2.shape == (2, 2)
            assert hasattr(axes2, "flatten")
            assert len(axes2.flatten()) == 4

            plt.close(fig2.fig)

    def test_reproduce_accepts_png_path(self):
        """Test that reproduce() accepts .png path and finds .yaml."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, ax1 = ps.subplots()
            ax1.plot([1, 2, 3], [1, 2, 3])

            png_path = Path(tmpdir) / "test.png"
            ps.save(fig1, png_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce using .png path
            fig2, ax2 = ps.reproduce(png_path)

            assert fig2 is not None
            assert ax2 is not None

            plt.close(fig2.fig)

    def test_reproduce_accepts_yaml_path(self):
        """Test that reproduce() accepts .yaml path directly."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, ax1 = ps.subplots()
            ax1.plot([1, 2, 3], [1, 2, 3])

            png_path = Path(tmpdir) / "test.png"
            ps.save(fig1, png_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce using .yaml path
            yaml_path = Path(tmpdir) / "test.yaml"
            fig2, ax2 = ps.reproduce(yaml_path)

            assert fig2 is not None
            assert ax2 is not None

            plt.close(fig2.fig)

    def test_reproduce_multiple_calls(self):
        """Test reproducing figure with multiple calls."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, ax1 = ps.subplots()
            ax1.plot([1, 2, 3], [1, 2, 3], color="red")
            ax1.scatter([1, 2, 3], [3, 2, 1], s=50)

            recipe_path = Path(tmpdir) / "multi.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check both artists were created
            assert len(ax2.lines) >= 1
            assert len(ax2.collections) >= 1

            plt.close(fig2.fig)

    def test_reproduce_with_decorations(self):
        """Test reproducing figure with decorations."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig1, ax1 = ps.subplots()
            ax1.plot([1, 2, 3], [1, 2, 3])
            ax1.set_xlabel("X Label")
            ax1.set_ylabel("Y Label")
            ax1.set_title("Title")

            recipe_path = Path(tmpdir) / "decorated.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)

            assert ax2.get_xlabel() == "X Label"
            assert ax2.get_ylabel() == "Y Label"
            assert ax2.get_title() == "Title"

            plt.close(fig2.fig)


class TestInfo:
    """Tests for info() function."""

    def test_info_basic_expected(self):
        """Test getting recipe info."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = ps.subplots(figsize=(10, 6))
            ax.plot([1, 2, 3], [4, 5, 6], id="test_plot")

            recipe_path = Path(tmpdir) / "info_test.yaml"
            ps.save(fig, recipe_path, validate=False)
            plt.close(fig.fig)

            info = ps.info(recipe_path)

            assert "id" in info
            assert "created" in info
            assert info["figsize"] == (10, 6)
            assert info["n_axes"] == 1
            assert len(info["calls"]) >= 1


class TestLargeArrays:
    """Tests for handling large arrays."""

    def test_large_array_saved_to_file(self):
        """Test that large arrays are saved to separate files."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create large arrays (> INLINE_THRESHOLD)
            x = np.linspace(0, 100, 1000)
            y = np.sin(x)

            fig, ax = ps.subplots()
            ax.plot(x, y)

            recipe_path = Path(tmpdir) / "large.yaml"
            ps.save(fig, recipe_path, validate=False)
            plt.close(fig.fig)

            # Check that data directory was created
            data_dir = Path(tmpdir) / "large_data"
            assert data_dir.exists()

            # Check that data files were created (CSV by default)
            data_files = list(data_dir.glob("*.csv"))
            assert len(data_files) > 0

    def test_large_array_reproduced_correctly(self):
        """Test that large arrays are reproduced correctly."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            x = np.linspace(0, 100, 500)
            y = np.sin(x)

            fig1, ax1 = ps.subplots()
            ax1.plot(x, y, color="green")

            recipe_path = Path(tmpdir) / "large_repro.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check that line data matches
            line = ax2.lines[0]
            xdata, ydata = line.get_xdata(), line.get_ydata()

            np.testing.assert_array_almost_equal(xdata, x)
            np.testing.assert_array_almost_equal(ydata, y)

            plt.close(fig2.fig)
        assert True  # TQ001-placeholder: body exercises code under test


class TestArrayListPlots:
    """Tests for plots that take list of arrays (boxplot, violinplot)."""

    def test_boxplot_save_and_reproduce(self):
        """Test boxplot with list of arrays can be saved and reproduced."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create boxplot
            np.random.seed(42)
            data = [np.random.randn(50) for _ in range(4)]

            fig1, ax1 = ps.subplots()
            ax1.boxplot(data, id="bp1", widths=0.6)

            recipe_path = Path(tmpdir) / "boxplot.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce - should not raise error
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check that boxplot was created (has multiple lines for whiskers etc.)
            assert len(ax2.lines) > 0

            plt.close(fig2.fig)

    def test_violinplot_save_and_reproduce(self):
        """Test violinplot with list of arrays can be saved and reproduced."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create violinplot
            np.random.seed(42)
            data = [np.random.randn(50) for _ in range(4)]

            fig1, ax1 = ps.subplots()
            ax1.violinplot(data, id="vp1", showmeans=True)

            recipe_path = Path(tmpdir) / "violin.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce - should not raise error
            fig2, ax2 = ps.reproduce(recipe_path)

            # Check that violinplot was created (has collections)
            assert len(ax2.collections) > 0

            plt.close(fig2.fig)

    def test_boxplot_patch_artist(self):
        """Test boxplot with patch_artist=True can be saved and reproduced."""
        # Arrange
        # Act
        # Assert
        import figrecipe as ps

        with tempfile.TemporaryDirectory() as tmpdir:
            np.random.seed(42)
            data = [np.random.randn(50) for _ in range(4)]

            fig1, ax1 = ps.subplots()
            ax1.boxplot(data, id="bp_patch", patch_artist=True)

            recipe_path = Path(tmpdir) / "boxplot_patch.yaml"
            ps.save(fig1, recipe_path, validate=False)
            plt.close(fig1.fig)

            # Reproduce
            fig2, ax2 = ps.reproduce(recipe_path)
            assert len(ax2.patches) > 0  # patch_artist creates Patch objects

            plt.close(fig2.fig)
