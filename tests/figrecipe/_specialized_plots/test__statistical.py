#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for specialized plot types."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr


class TestSpecializedPlotsImports:
    """Test module import patterns."""

    def test_import_from_submodule_part_1(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(heatmap)

    def test_import_from_submodule_part_2(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(conf_mat)

    def test_import_from_submodule_part_3(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(ecdf)

    def test_import_from_submodule_part_4(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(shaded_line)

    def test_import_from_submodule_part_5(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(mean_std_line)

    def test_import_from_submodule_part_6(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(mean_ci_line)

    def test_import_from_submodule_part_7(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(median_iqr_line)

    def test_import_from_submodule_part_8(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(raster)

    def test_import_from_submodule_part_9(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(fillv)

    def test_import_from_submodule_part_10(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(fillh)

    def test_import_from_submodule_part_11(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(rectangle)

    def test_import_from_submodule_part_12(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(vline)

    def test_import_from_submodule_part_13(self):
        """Test importing from specialized_plots submodule."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import (
            conf_mat,
            ecdf,
            fillh,
            fillv,
            heatmap,
            hline,
            mean_ci_line,
            mean_std_line,
            median_iqr_line,
            raster,
            rectangle,
            shaded_line,
            vline,
        )
        assert callable(hline)


class TestHeatmap:
    """Test heatmap function."""

    def test_basic_heatmap_part_1(self):
        """Test basic heatmap creation."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap
        fig, ax = fr.subplots()
        data = np.random.rand(5, 10)
        ax_out, im, cbar = heatmap(ax, data)
        assert ax_out is not None

    def test_basic_heatmap_part_2(self):
        """Test basic heatmap creation."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap
        fig, ax = fr.subplots()
        data = np.random.rand(5, 10)
        ax_out, im, cbar = heatmap(ax, data)
        assert im is not None

    def test_basic_heatmap_part_3(self):
        """Test basic heatmap creation."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap
        fig, ax = fr.subplots()
        data = np.random.rand(5, 10)
        ax_out, im, cbar = heatmap(ax, data)
        assert cbar is not None

    def test_heatmap_with_labels(self):
        """Test heatmap with custom labels."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(3, 4)
        x_labels = ["A", "B", "C", "D"]
        y_labels = ["X", "Y", "Z"]

        ax_out, im, cbar = heatmap(ax, data, x_labels=x_labels, y_labels=y_labels)

        assert ax_out is not None
        plt.close("all")

    def test_heatmap_no_annotation(self):
        """Test heatmap without annotations."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(4, 4)

        ax_out, im, cbar = heatmap(ax, data, show_annot=False)

        assert ax_out is not None
        plt.close("all")

    def test_heatmap_custom_cmap(self):
        """Test heatmap with custom colormap."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(3, 3)

        ax_out, im, cbar = heatmap(ax, data, cmap="Blues", cbar_label="Values")

        assert ax_out is not None
        plt.close("all")


class TestConfMat:
    """Test confusion matrix function."""

    def test_basic_conf_mat_part_1(self):
        """Test basic confusion matrix."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import conf_mat
        fig, ax = fr.subplots()
        data = np.array([[45, 5, 2], [3, 42, 8], [1, 6, 48]])
        result = conf_mat(ax, data, calc_bacc=True)
        assert len(result) == 2

    def test_basic_conf_mat_part_2(self):
        """Test basic confusion matrix."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import conf_mat
        fig, ax = fr.subplots()
        data = np.array([[45, 5, 2], [3, 42, 8], [1, 6, 48]])
        result = conf_mat(ax, data, calc_bacc=True)
        ax_out, bacc = result
        assert ax_out is not None

    def test_basic_conf_mat_part_3(self):
        """Test basic confusion matrix."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import conf_mat
        fig, ax = fr.subplots()
        data = np.array([[45, 5, 2], [3, 42, 8], [1, 6, 48]])
        result = conf_mat(ax, data, calc_bacc=True)
        ax_out, bacc = result
        assert 0 <= bacc <= 1

    def test_conf_mat_with_labels(self):
        """Test confusion matrix with labels."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import conf_mat

        fig, ax = fr.subplots()
        data = np.array([[10, 2], [3, 15]])
        x_labels = ["Pred A", "Pred B"]
        y_labels = ["True A", "True B"]

        ax_out, bacc = conf_mat(ax, data, x_labels=x_labels, y_labels=y_labels)

        assert ax_out is not None
        plt.close("all")

    def test_conf_mat_no_bacc(self):
        """Test confusion matrix without balanced accuracy."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import conf_mat

        fig, ax = fr.subplots()
        data = np.array([[10, 2], [3, 15]])

        ax_out = conf_mat(ax, data, calc_bacc=False)

        # Should return just ax, not tuple
        assert ax_out is not None
        plt.close("all")


class TestECDF:
    """Test ECDF function."""

    def test_basic_ecdf_part_1(self):
        """Test basic ECDF plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.random.randn(100)
        ax_out, ecdf_data = ecdf(ax, data)
        assert ax_out is not None

    def test_basic_ecdf_part_2(self):
        """Test basic ECDF plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.random.randn(100)
        ax_out, ecdf_data = ecdf(ax, data)
        assert "x" in ecdf_data

    def test_basic_ecdf_part_3(self):
        """Test basic ECDF plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.random.randn(100)
        ax_out, ecdf_data = ecdf(ax, data)
        assert "y" in ecdf_data

    def test_basic_ecdf_part_4(self):
        """Test basic ECDF plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.random.randn(100)
        ax_out, ecdf_data = ecdf(ax, data)
        assert "n" in ecdf_data

    def test_basic_ecdf_part_5(self):
        """Test basic ECDF plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.random.randn(100)
        ax_out, ecdf_data = ecdf(ax, data)
        assert ecdf_data["n"] == 100

    def test_ecdf_with_nan_warns_user(self):
        """ECDF on data containing NaN must emit a UserWarning."""
        # Arrange
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        # Act
        ctx = pytest.warns(UserWarning, match="NaN values")
        # Assert
        with ctx:
            ecdf(ax, data)

    def test_ecdf_with_nan_excludes_nan_from_count(self):
        """ECDF on data containing NaN must drop the NaN from `n`."""
        # Arrange
        import warnings
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        # Act
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _ax_out, ecdf_data = ecdf(ax, data)
        # Assert
        assert ecdf_data["n"] == 4

    def test_ecdf_empty_after_nan_removal_warns_user(self):
        """ECDF on all-NaN data must emit a UserWarning."""
        # Arrange
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.array([np.nan, np.nan])
        # Act
        ctx = pytest.warns(UserWarning)
        # Assert
        with ctx:
            ecdf(ax, data)

    def test_ecdf_empty_after_nan_removal_has_zero_count(self):
        """ECDF on all-NaN data must report `n == 0`."""
        # Arrange
        import warnings
        from figrecipe._specialized_plots import ecdf
        fig, ax = fr.subplots()
        data = np.array([np.nan, np.nan])
        # Act
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _ax_out, ecdf_data = ecdf(ax, data)
        # Assert
        assert ecdf_data["n"] == 0


class TestShadedLine:
    """Test shaded line functions."""

    def test_basic_shaded_line_part_1(self):
        """Test basic shaded line plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import shaded_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_mean = np.sin(x)
        y_std = 0.2
        ax_out, data = shaded_line(
            ax, x, y_mean - y_std, y_mean, y_mean + y_std, color="blue"
        )
        assert ax_out is not None

    def test_basic_shaded_line_part_2(self):
        """Test basic shaded line plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import shaded_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_mean = np.sin(x)
        y_std = 0.2
        ax_out, data = shaded_line(
            ax, x, y_mean - y_std, y_mean, y_mean + y_std, color="blue"
        )
        assert "x" in data

    def test_basic_shaded_line_part_3(self):
        """Test basic shaded line plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import shaded_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_mean = np.sin(x)
        y_std = 0.2
        ax_out, data = shaded_line(
            ax, x, y_mean - y_std, y_mean, y_mean + y_std, color="blue"
        )
        assert "y_middle" in data

    def test_mean_std_line_part_1(self):
        """Test mean with std bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_std_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_std_line(ax, x, y_samples, axis=0)
        assert ax_out is not None

    def test_mean_std_line_part_2(self):
        """Test mean with std bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_std_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_std_line(ax, x, y_samples, axis=0)
        assert "std" in data

    def test_mean_std_line_part_3(self):
        """Test mean with std bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_std_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_std_line(ax, x, y_samples, axis=0)
        assert "n_samples" in data

    def test_mean_ci_line_part_1(self):
        """Test mean with CI bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_ci_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_ci_line(ax, x, y_samples, axis=0, ci=95.0)
        assert ax_out is not None

    def test_mean_ci_line_part_2(self):
        """Test mean with CI bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_ci_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_ci_line(ax, x, y_samples, axis=0, ci=95.0)
        assert "ci" in data

    def test_mean_ci_line_part_3(self):
        """Test mean with CI bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import mean_ci_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = mean_ci_line(ax, x, y_samples, axis=0, ci=95.0)
        assert data["ci"] == 95.0

    def test_median_iqr_line_part_1(self):
        """Test median with IQR bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import median_iqr_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = median_iqr_line(ax, x, y_samples, axis=0)
        assert ax_out is not None

    def test_median_iqr_line_part_2(self):
        """Test median with IQR bands."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import median_iqr_line
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2
        ax_out, data = median_iqr_line(ax, x, y_samples, axis=0)
        assert "n_samples" in data


class TestRaster:
    """Test raster plot function."""

    def test_basic_raster_part_1(self):
        """Test basic raster plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster
        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]
        ax_out, data = raster(ax, spike_times)
        assert ax_out is not None

    def test_basic_raster_part_2(self):
        """Test basic raster plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster
        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]
        ax_out, data = raster(ax, spike_times)
        assert "spike_times" in data

    def test_basic_raster_part_3(self):
        """Test basic raster plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster
        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]
        ax_out, data = raster(ax, spike_times)
        assert "digital" in data

    def test_basic_raster_part_4(self):
        """Test basic raster plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster
        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]
        ax_out, data = raster(ax, spike_times)
        assert "n_trials" in data

    def test_basic_raster_part_5(self):
        """Test basic raster plot."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster
        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]
        ax_out, data = raster(ax, spike_times)
        assert data["n_trials"] == 10

    def test_raster_with_colors(self):
        """Test raster with custom colors."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import raster

        fig, ax = fr.subplots()
        spike_times = [[1, 5, 10], [2, 8, 15], [3, 7, 12]]
        colors = ["red", "green", "blue"]

        ax_out, data = raster(ax, spike_times, colors=colors)

        assert ax_out is not None
        plt.close("all")


class TestAnnotationHelpers:
    """Test annotation helper functions."""

    def test_fillv_annotation_helpers(self):
        """Test vertical fill regions."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import fillv

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = fillv(ax, [2, 6], [4, 8], color="blue", alpha=0.3)

        assert ax_out is not None
        plt.close("all")

    def test_fillh_annotation_helpers(self):
        """Test horizontal fill regions."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import fillh

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = fillh(ax, [-0.5], [0.5], color="green", alpha=0.2)

        assert ax_out is not None
        plt.close("all")

    def test_rectangle_part_1(self):
        """Test rectangle annotation."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import rectangle
        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))
        ax_out, rect = rectangle(ax, 2, -0.5, 2, 1.0, color="red", alpha=0.2)
        assert ax_out is not None

    def test_rectangle_part_2(self):
        """Test rectangle annotation."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import rectangle
        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))
        ax_out, rect = rectangle(ax, 2, -0.5, 2, 1.0, color="red", alpha=0.2)
        assert rect is not None

    def test_vline_annotation_helpers(self):
        """Test vertical lines."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import vline

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = vline(ax, [2, 5, 8], color="red", linestyle="--")

        assert ax_out is not None
        plt.close("all")

    def test_hline_annotation_helpers(self):
        """Test horizontal lines."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import hline

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = hline(ax, [0, 0.5, -0.5], color="blue", linestyle=":")

        assert ax_out is not None
        plt.close("all")

    def test_fillv_on_array_part_1(self):
        """Test fillv on array of axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import fillv
        fig, axes = fr.subplots(1, 3)
        for ax in axes.flatten():
            ax.plot([0, 10], [0, 1])
        result = fillv(axes, [2], [4], color="red")
        assert isinstance(result, list)

    def test_fillv_on_array_part_2(self):
        """Test fillv on array of axes."""
        # Arrange
        # Act
        # Assert
        from figrecipe._specialized_plots import fillv
        fig, axes = fr.subplots(1, 3)
        for ax in axes.flatten():
            ax.plot([0, 10], [0, 1])
        result = fillv(axes, [2], [4], color="red")
        assert len(result) == 3


# EOF
