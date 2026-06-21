#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for CSV format options (single vs separate)."""

import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import figrecipe as fr


class TestCsvFormat:
    """Tests for csv_format parameter."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        """Reset matplotlib state before and after each test."""
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    @pytest.fixture
    def tmpdir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_save_separate_csv_default_part_1(self, tmpdir):
        """Test that default csv_format='separate' creates per-variable CSV files.

        Note: Uses > 100 data points to exceed INLINE_THRESHOLD and trigger file storage.
        """
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 150)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path)
        data_dir = tmpdir / "test_data"
        assert data_dir.exists()

    def test_save_separate_csv_default_part_2(self, tmpdir):
        """Test that default csv_format='separate' creates per-variable CSV files.

        Note: Uses > 100 data points to exceed INLINE_THRESHOLD and trigger file storage.
        """
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 150)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path)
        data_dir = tmpdir / "test_data"
        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) >= 2

    def test_save_single_csv_format_part_1(self, tmpdir):
        """Test that csv_format='single' creates a single CSV file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")
        csv_path = tmpdir / "test.csv"
        assert csv_path.exists()

    def test_save_single_csv_format_part_2(self, tmpdir):
        """Test that csv_format='single' creates a single CSV file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")
        csv_path = tmpdir / "test.csv"
        data_dir = tmpdir / "test_data"
        assert not data_dir.exists()

    def test_save_single_csv_format_part_3(self, tmpdir):
        """Test that csv_format='single' creates a single CSV file."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")
        csv_path = tmpdir / "test.csv"
        data_dir = tmpdir / "test_data"
        import pandas as pd

        df = pd.read_csv(csv_path)
        assert len(df.columns) >= 2

    def test_single_csv_column_naming_part_1(self, tmpdir):
        """Test that single CSV uses short column naming format."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        ax.plot(x, y, id="my_trace")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "test.csv")
        assert "r0c0_my-trace_x" in df.columns

    def test_single_csv_column_naming_part_2(self, tmpdir):
        """Test that single CSV uses short column naming format."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        ax.plot(x, y, id="my_trace")
        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "test.csv")
        assert "r0c0_my-trace_y" in df.columns

    def test_single_csv_roundtrip_part_1(self, tmpdir):
        """Test full round-trip with single CSV format."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 2 * np.pi, 100)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        ax.set_xlabel("X axis")
        ax.set_ylabel("Y axis")
        output_path = tmpdir / "roundtrip.yaml"
        fr.save(fig, output_path, csv_format="single")
        plt.close("all")
        fig2, ax2 = fr.reproduce(output_path)
        assert fig2 is not None

    def test_single_csv_roundtrip_part_2(self, tmpdir):
        """Test full round-trip with single CSV format."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 2 * np.pi, 100)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        ax.set_xlabel("X axis")
        ax.set_ylabel("Y axis")
        output_path = tmpdir / "roundtrip.yaml"
        fr.save(fig, output_path, csv_format="single")
        plt.close("all")
        fig2, ax2 = fr.reproduce(output_path)
        assert ax2 is not None

    def test_single_csv_roundtrip_data_integrity(self, tmpdir):
        """Test that data survives round-trip with single CSV format."""
        # Create original figure
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x_orig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_orig = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        ax.plot(x_orig, y_orig, id="squares")

        # Save with single CSV format
        output_path = tmpdir / "data_test.yaml"
        fr.save(fig, output_path, csv_format="single")
        plt.close("all")

        # Load the CSV directly and verify data
        import pandas as pd

        df = pd.read_csv(tmpdir / "data_test.csv")

        x_loaded = df["r0c0_squares_x"].values
        y_loaded = df["r0c0_squares_y"].values

        np.testing.assert_array_almost_equal(x_loaded, x_orig)
        np.testing.assert_array_almost_equal(y_loaded, y_orig)
        assert True  # TQ001-placeholder: body exercises code under test

    def test_single_csv_multi_trace_part_1(self, tmpdir):
        """Test single CSV format with multiple traces."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")
        output_path = tmpdir / "multi.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "multi.csv")
        assert "r0c0_sine_x" in df.columns

    def test_single_csv_multi_trace_part_2(self, tmpdir):
        """Test single CSV format with multiple traces."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")
        output_path = tmpdir / "multi.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "multi.csv")
        assert "r0c0_sine_y" in df.columns

    def test_single_csv_multi_trace_part_3(self, tmpdir):
        """Test single CSV format with multiple traces."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")
        output_path = tmpdir / "multi.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "multi.csv")
        assert "r0c0_cosine_x" in df.columns

    def test_single_csv_multi_trace_part_4(self, tmpdir):
        """Test single CSV format with multiple traces."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")
        output_path = tmpdir / "multi.yaml"
        fr.save(fig, output_path, csv_format="single")
        import pandas as pd

        df = pd.read_csv(tmpdir / "multi.csv")
        assert "r0c0_cosine_y" in df.columns

    def test_single_csv_multi_axes_part_1(self, tmpdir):
        """Test single CSV format with multiple axes."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        x = np.linspace(0, 10, 50)
        axes[0].plot(x, np.sin(x), id="left_plot")
        axes[1].plot(x, np.cos(x), id="right_plot")
        output_path = tmpdir / "multiax.yaml"
        fr.save(fig, output_path, csv_format="single", validate=False)
        import pandas as pd

        df = pd.read_csv(tmpdir / "multiax.csv")
        assert "r0c0_left-plot_x" in df.columns

    def test_single_csv_multi_axes_part_2(self, tmpdir):
        """Test single CSV format with multiple axes."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        x = np.linspace(0, 10, 50)
        axes[0].plot(x, np.sin(x), id="left_plot")
        axes[1].plot(x, np.cos(x), id="right_plot")
        output_path = tmpdir / "multiax.yaml"
        fr.save(fig, output_path, csv_format="single", validate=False)
        import pandas as pd

        df = pd.read_csv(tmpdir / "multiax.csv")
        assert "r0c0_left-plot_y" in df.columns

    def test_single_csv_multi_axes_part_3(self, tmpdir):
        """Test single CSV format with multiple axes."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        x = np.linspace(0, 10, 50)
        axes[0].plot(x, np.sin(x), id="left_plot")
        axes[1].plot(x, np.cos(x), id="right_plot")
        output_path = tmpdir / "multiax.yaml"
        fr.save(fig, output_path, csv_format="single", validate=False)
        import pandas as pd

        df = pd.read_csv(tmpdir / "multiax.csv")
        assert "r0c1_right-plot_x" in df.columns

    def test_single_csv_multi_axes_part_4(self, tmpdir):
        """Test single CSV format with multiple axes."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        x = np.linspace(0, 10, 50)
        axes[0].plot(x, np.sin(x), id="left_plot")
        axes[1].plot(x, np.cos(x), id="right_plot")
        output_path = tmpdir / "multiax.yaml"
        fr.save(fig, output_path, csv_format="single", validate=False)
        import pandas as pd

        df = pd.read_csv(tmpdir / "multiax.csv")
        assert "r0c1_right-plot_y" in df.columns


class TestCsvFormatLoadSingleCsv:
    """Tests for load_single_csv function."""

    @pytest.fixture
    def tmpdir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_load_short_format_part_1(self, tmpdir):
        """Test loading CSV with short format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "r0c0_trace1_x": [1, 2, 3],
                "r0c0_trace1_y": [4, 5, 6],
                "r0c1_trace2_x": [7, 8, 9],
                "r0c1_trace2_y": [10, 11, 12],
            }
        )
        csv_path = tmpdir / "short_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "r0c0" in result

    def test_load_short_format_part_2(self, tmpdir):
        """Test loading CSV with short format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "r0c0_trace1_x": [1, 2, 3],
                "r0c0_trace1_y": [4, 5, 6],
                "r0c1_trace2_x": [7, 8, 9],
                "r0c1_trace2_y": [10, 11, 12],
            }
        )
        csv_path = tmpdir / "short_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "r0c1" in result

    def test_load_short_format_part_3(self, tmpdir):
        """Test loading CSV with short format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "r0c0_trace1_x": [1, 2, 3],
                "r0c0_trace1_y": [4, 5, 6],
                "r0c1_trace2_x": [7, 8, 9],
                "r0c1_trace2_y": [10, 11, 12],
            }
        )
        csv_path = tmpdir / "short_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "trace1" in result["r0c0"]

    def test_load_short_format_part_4(self, tmpdir):
        """Test loading CSV with short format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "r0c0_trace1_x": [1, 2, 3],
                "r0c0_trace1_y": [4, 5, 6],
                "r0c1_trace2_x": [7, 8, 9],
                "r0c1_trace2_y": [10, 11, 12],
            }
        )
        csv_path = tmpdir / "short_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "trace2" in result["r0c1"]

    def test_load_legacy_format_part_1(self, tmpdir):
        """Test loading CSV with legacy format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "ax-row-0-col-0_trace-id-trace1_variable-x": [1, 2, 3],
                "ax-row-0-col-0_trace-id-trace1_variable-y": [4, 5, 6],
            }
        )
        csv_path = tmpdir / "legacy_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "r0c0" in result

    def test_load_legacy_format_part_2(self, tmpdir):
        """Test loading CSV with legacy format column names."""
        # Arrange
        # Act
        # Assert
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        df = pd.DataFrame(
            {
                "ax-row-0-col-0_trace-id-trace1_variable-x": [1, 2, 3],
                "ax-row-0-col-0_trace-id-trace1_variable-y": [4, 5, 6],
            }
        )
        csv_path = tmpdir / "legacy_format.csv"
        df.to_csv(csv_path, index=False)
        result = load_single_csv(csv_path)
        assert "trace1" in result["r0c0"]


def _trace_axes():
    """An axis-off trace panel, like an iEEG strip."""
    fig, ax = plt.subplots()
    t = np.linspace(0, 600, 600)  # 600 s
    ax.plot(t, np.sin(t / 20.0) * 50)
    ax.axis("off")
    return fig, ax


class TestScalebar:
    """Tests for the L-shaped stx_scalebar primitive."""

    @pytest.fixture(autouse=True)
    def reset_matplotlib(self):
        plt.close("all")
        matplotlib.rcdefaults()
        yield
        plt.close("all")

    def test_returns_same_axes(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        # Act
        out = stx_scalebar(ax, 60, 100, x_label="1 min", y_label="unknown")
        # Assert
        assert out is ax

    def test_draws_two_arms(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        n_before = len(ax.lines)
        # Act
        stx_scalebar(ax, 60, 100, x_label="1 min", y_label="unknown")
        # Assert
        assert len(ax.lines) == n_before + 2

    def test_horizontal_arm_spans_x_len(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        # Act
        stx_scalebar(ax, 60, 100)
        horiz = ax.lines[-2]
        hx, hy = horiz.get_xdata(), horiz.get_ydata()
        # Assert
        assert hy[0] == hy[1] and np.isclose(abs(hx[1] - hx[0]), 60)

    def test_vertical_arm_spans_y_len(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        # Act
        stx_scalebar(ax, 60, 100)
        vert = ax.lines[-1]
        vx, vy = vert.get_xdata(), vert.get_ydata()
        # Assert
        assert vx[0] == vx[1] and np.isclose(abs(vy[1] - vy[0]), 100)

    def test_arms_share_a_vertex(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        # Act
        stx_scalebar(ax, 60, 100)
        horiz, vert = ax.lines[-2], ax.lines[-1]
        # Assert
        assert np.isclose(horiz.get_xdata()[0], vert.get_xdata()[0]) and np.isclose(
            horiz.get_ydata()[0], vert.get_ydata()[0]
        )

    def test_arms_are_black(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        # Act
        stx_scalebar(ax, 60, 100, color="black")
        arms = ax.lines[-2:]
        # Assert
        assert all(matplotlib.colors.to_hex(ln.get_color()) == "#000000" for ln in arms)

    def test_two_labels_with_expected_text(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        n_txt = len(ax.texts)
        # Act
        stx_scalebar(ax, 60, 100, x_label="1 min", y_label="unknown")
        labels = {t.get_text() for t in ax.texts[n_txt:]}
        # Assert
        assert labels == {"1 min", "unknown"}

    def test_labels_do_not_overlap(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        n_txt = len(ax.texts)
        # Act
        stx_scalebar(ax, 60, 100, x_label="1 min", y_label="unknown")
        by_text = {t.get_text(): t.get_position() for t in ax.texts[n_txt:]}
        # Assert
        assert by_text["1 min"] != by_text["unknown"]

    def test_y_label_is_rotated_vertical(self):
        # Arrange
        from figrecipe._scitex_compat._simple import stx_scalebar

        _, ax = _trace_axes()
        n_txt = len(ax.texts)
        # Act
        stx_scalebar(ax, 60, 100, x_label="1 min", y_label="unknown")
        by_text = {t.get_text(): t for t in ax.texts[n_txt:]}
        # Assert
        assert by_text["unknown"].get_rotation() == 90

    def test_no_hardcoded_fontsize(self):
        # Arrange: labels should inherit the rcParams font size.
        from figrecipe._scitex_compat._simple import stx_scalebar

        matplotlib.rcParams["font.size"] = 7.0
        _, ax = _trace_axes()
        n_txt = len(ax.texts)
        # Act
        stx_scalebar(ax, 60, 100)
        # Assert
        assert all(t.get_fontsize() == 7.0 for t in ax.texts[n_txt:])

    def test_recording_axes_method(self):
        # Arrange
        fig, ax = fr.subplots()
        ax.plot(np.linspace(0, 600, 600), np.zeros(600))
        ax.axis("off")
        # Act
        out = ax.stx_scalebar(60, 100, x_label="1 min", y_label="unknown")
        # Assert
        assert out is not None
