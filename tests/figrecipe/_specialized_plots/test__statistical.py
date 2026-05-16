#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for specialized plot types."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr


class TestSpecializedPlotsImports:
    """Test module import patterns."""

    def test_import_from_submodule(self):
        """Test importing from specialized_plots submodule."""
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
        assert callable(conf_mat)
        assert callable(ecdf)
        assert callable(shaded_line)
        assert callable(mean_std_line)
        assert callable(mean_ci_line)
        assert callable(median_iqr_line)
        assert callable(raster)
        assert callable(fillv)
        assert callable(fillh)
        assert callable(rectangle)
        assert callable(vline)
        assert callable(hline)


class TestHeatmap:
    """Test heatmap function."""

    def test_basic_heatmap(self):
        """Test basic heatmap creation."""
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(5, 10)
        ax_out, im, cbar = heatmap(ax, data)

        assert ax_out is not None
        assert im is not None
        assert cbar is not None
        plt.close("all")

    def test_heatmap_with_labels(self):
        """Test heatmap with custom labels."""
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
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(4, 4)

        ax_out, im, cbar = heatmap(ax, data, show_annot=False)

        assert ax_out is not None
        plt.close("all")

    def test_heatmap_custom_cmap(self):
        """Test heatmap with custom colormap."""
        from figrecipe._specialized_plots import heatmap

        fig, ax = fr.subplots()
        data = np.random.rand(3, 3)

        ax_out, im, cbar = heatmap(ax, data, cmap="Blues", cbar_label="Values")

        assert ax_out is not None
        plt.close("all")


class TestConfMat:
    """Test confusion matrix function."""

    def test_basic_conf_mat(self):
        """Test basic confusion matrix."""
        from figrecipe._specialized_plots import conf_mat

        fig, ax = fr.subplots()
        data = np.array([[45, 5, 2], [3, 42, 8], [1, 6, 48]])

        result = conf_mat(ax, data, calc_bacc=True)

        assert len(result) == 2
        ax_out, bacc = result
        assert ax_out is not None
        assert 0 <= bacc <= 1
        plt.close("all")

    def test_conf_mat_with_labels(self):
        """Test confusion matrix with labels."""
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
        from figrecipe._specialized_plots import conf_mat

        fig, ax = fr.subplots()
        data = np.array([[10, 2], [3, 15]])

        ax_out = conf_mat(ax, data, calc_bacc=False)

        # Should return just ax, not tuple
        assert ax_out is not None
        plt.close("all")


class TestECDF:
    """Test ECDF function."""

    def test_basic_ecdf(self):
        """Test basic ECDF plot."""
        from figrecipe._specialized_plots import ecdf

        fig, ax = fr.subplots()
        data = np.random.randn(100)

        ax_out, ecdf_data = ecdf(ax, data)

        assert ax_out is not None
        assert "x" in ecdf_data
        assert "y" in ecdf_data
        assert "n" in ecdf_data
        assert ecdf_data["n"] == 100
        plt.close("all")

    def test_ecdf_with_nan(self):
        """Test ECDF handles NaN values."""
        from figrecipe._specialized_plots import ecdf

        fig, ax = fr.subplots()
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])

        with pytest.warns(UserWarning, match="NaN values"):
            ax_out, ecdf_data = ecdf(ax, data)

        assert ecdf_data["n"] == 4  # NaN excluded
        plt.close("all")

    def test_ecdf_empty(self):
        """Test ECDF with empty data after NaN removal."""
        from figrecipe._specialized_plots import ecdf

        fig, ax = fr.subplots()
        data = np.array([np.nan, np.nan])

        with pytest.warns(UserWarning):
            ax_out, ecdf_data = ecdf(ax, data)

        assert ecdf_data["n"] == 0
        plt.close("all")


class TestShadedLine:
    """Test shaded line functions."""

    def test_basic_shaded_line(self):
        """Test basic shaded line plot."""
        from figrecipe._specialized_plots import shaded_line

        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_mean = np.sin(x)
        y_std = 0.2

        ax_out, data = shaded_line(
            ax, x, y_mean - y_std, y_mean, y_mean + y_std, color="blue"
        )

        assert ax_out is not None
        assert "x" in data
        assert "y_middle" in data
        plt.close("all")

    def test_mean_std_line(self):
        """Test mean with std bands."""
        from figrecipe._specialized_plots import mean_std_line

        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2

        ax_out, data = mean_std_line(ax, x, y_samples, axis=0)

        assert ax_out is not None
        assert "std" in data
        assert "n_samples" in data
        plt.close("all")

    def test_mean_ci_line(self):
        """Test mean with CI bands."""
        from figrecipe._specialized_plots import mean_ci_line

        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2

        ax_out, data = mean_ci_line(ax, x, y_samples, axis=0, ci=95.0)

        assert ax_out is not None
        assert "ci" in data
        assert data["ci"] == 95.0
        plt.close("all")

    def test_median_iqr_line(self):
        """Test median with IQR bands."""
        from figrecipe._specialized_plots import median_iqr_line

        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y_samples = np.sin(x) + np.random.randn(20, 50) * 0.2

        ax_out, data = median_iqr_line(ax, x, y_samples, axis=0)

        assert ax_out is not None
        assert "n_samples" in data
        plt.close("all")


class TestRaster:
    """Test raster plot function."""

    def test_basic_raster(self):
        """Test basic raster plot."""
        from figrecipe._specialized_plots import raster

        fig, ax = fr.subplots()
        np.random.seed(42)
        spike_times = [
            np.sort(np.random.choice(100, np.random.randint(5, 20), replace=False))
            for _ in range(10)
        ]

        ax_out, data = raster(ax, spike_times)

        assert ax_out is not None
        assert "spike_times" in data
        assert "digital" in data
        assert "n_trials" in data
        assert data["n_trials"] == 10
        plt.close("all")

    def test_raster_with_colors(self):
        """Test raster with custom colors."""
        from figrecipe._specialized_plots import raster

        fig, ax = fr.subplots()
        spike_times = [[1, 5, 10], [2, 8, 15], [3, 7, 12]]
        colors = ["red", "green", "blue"]

        ax_out, data = raster(ax, spike_times, colors=colors)

        assert ax_out is not None
        plt.close("all")


class TestAnnotationHelpers:
    """Test annotation helper functions."""

    def test_fillv(self):
        """Test vertical fill regions."""
        from figrecipe._specialized_plots import fillv

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = fillv(ax, [2, 6], [4, 8], color="blue", alpha=0.3)

        assert ax_out is not None
        plt.close("all")

    def test_fillh(self):
        """Test horizontal fill regions."""
        from figrecipe._specialized_plots import fillh

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = fillh(ax, [-0.5], [0.5], color="green", alpha=0.2)

        assert ax_out is not None
        plt.close("all")

    def test_rectangle(self):
        """Test rectangle annotation."""
        from figrecipe._specialized_plots import rectangle

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out, rect = rectangle(ax, 2, -0.5, 2, 1.0, color="red", alpha=0.2)

        assert ax_out is not None
        assert rect is not None
        plt.close("all")

    def test_vline(self):
        """Test vertical lines."""
        from figrecipe._specialized_plots import vline

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = vline(ax, [2, 5, 8], color="red", linestyle="--")

        assert ax_out is not None
        plt.close("all")

    def test_hline(self):
        """Test horizontal lines."""
        from figrecipe._specialized_plots import hline

        fig, ax = fr.subplots()
        t = np.linspace(0, 10, 100)
        ax.plot(t, np.sin(t))

        ax_out = hline(ax, [0, 0.5, -0.5], color="blue", linestyle=":")

        assert ax_out is not None
        plt.close("all")

    def test_fillv_on_array(self):
        """Test fillv on array of axes."""
        from figrecipe._specialized_plots import fillv

        fig, axes = fr.subplots(1, 3)
        for ax in axes.flatten():
            ax.plot([0, 10], [0, 1])

        result = fillv(axes, [2], [4], color="red")

        assert isinstance(result, list)
        assert len(result) == 3
        plt.close("all")


# EOF
