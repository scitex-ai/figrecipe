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

    def test_save_separate_csv_default(self, tmpdir):
        """Test that default csv_format='separate' creates per-variable CSV files.

        Note: Uses > 100 data points to exceed INLINE_THRESHOLD and trigger file storage.
        """
        fig, ax = fr.subplots()
        # Use > 100 points to exceed INLINE_THRESHOLD
        x = np.linspace(0, 10, 150)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")

        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path)

        # Check that data directory was created with separate CSVs
        data_dir = tmpdir / "test_data"
        assert data_dir.exists()

        # Should have CSV files for x and y
        csv_files = list(data_dir.glob("*.csv"))
        assert len(csv_files) >= 2

        plt.close("all")

    def test_save_single_csv_format(self, tmpdir):
        """Test that csv_format='single' creates a single CSV file."""
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")

        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")

        # Check that single CSV was created
        csv_path = tmpdir / "test.csv"
        assert csv_path.exists()

        # Data directory should NOT exist for single format
        data_dir = tmpdir / "test_data"
        assert not data_dir.exists()

        # Read CSV and check column names
        import pandas as pd

        df = pd.read_csv(csv_path)

        # Should have short format column names: r0c0_{trace_id}_{var}
        assert len(df.columns) >= 2
        # Check that column names follow short format
        for col in df.columns:
            assert col.startswith("r0c0_")

        plt.close("all")

    def test_single_csv_column_naming(self, tmpdir):
        """Test that single CSV uses short column naming format."""
        fig, ax = fr.subplots()
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        ax.plot(x, y, id="my_trace")

        output_path = tmpdir / "test.yaml"
        fr.save(fig, output_path, csv_format="single")

        import pandas as pd

        df = pd.read_csv(tmpdir / "test.csv")

        # Column names should be r0c0_my-trace_x and r0c0_my-trace_y
        assert "r0c0_my-trace_x" in df.columns
        assert "r0c0_my-trace_y" in df.columns

        plt.close("all")

    def test_single_csv_roundtrip(self, tmpdir):
        """Test full round-trip with single CSV format."""
        # Create original figure
        fig, ax = fr.subplots()
        x = np.linspace(0, 2 * np.pi, 100)
        y = np.sin(x)
        ax.plot(x, y, id="sine_wave")
        ax.set_xlabel("X axis")
        ax.set_ylabel("Y axis")

        # Save with single CSV format
        output_path = tmpdir / "roundtrip.yaml"
        fr.save(fig, output_path, csv_format="single")
        plt.close("all")

        # Reproduce
        fig2, ax2 = fr.reproduce(output_path)

        # Check that figure was reproduced (basic sanity check)
        assert fig2 is not None
        assert ax2 is not None

        plt.close("all")

    def test_single_csv_roundtrip_data_integrity(self, tmpdir):
        """Test that data survives round-trip with single CSV format."""
        # Create original figure
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

    def test_single_csv_multi_trace(self, tmpdir):
        """Test single CSV format with multiple traces."""
        fig, ax = fr.subplots()
        x = np.linspace(0, 10, 50)
        ax.plot(x, np.sin(x), id="sine")
        ax.plot(x, np.cos(x), id="cosine")

        output_path = tmpdir / "multi.yaml"
        fr.save(fig, output_path, csv_format="single")

        import pandas as pd

        df = pd.read_csv(tmpdir / "multi.csv")

        # Should have 4 columns: sine_x, sine_y, cosine_x, cosine_y
        assert "r0c0_sine_x" in df.columns
        assert "r0c0_sine_y" in df.columns
        assert "r0c0_cosine_x" in df.columns
        assert "r0c0_cosine_y" in df.columns

        plt.close("all")

    def test_single_csv_multi_axes(self, tmpdir):
        """Test single CSV format with multiple axes."""
        fig, axes = fr.subplots(1, 2)
        x = np.linspace(0, 10, 50)
        axes[0].plot(x, np.sin(x), id="left_plot")
        axes[1].plot(x, np.cos(x), id="right_plot")

        output_path = tmpdir / "multiax.yaml"
        # Disable validation - this test only checks CSV format, not reproducibility
        fr.save(fig, output_path, csv_format="single", validate=False)

        import pandas as pd

        df = pd.read_csv(tmpdir / "multiax.csv")

        # Should have columns for both axes
        assert "r0c0_left-plot_x" in df.columns
        assert "r0c0_left-plot_y" in df.columns
        assert "r0c1_right-plot_x" in df.columns
        assert "r0c1_right-plot_y" in df.columns

        plt.close("all")


class TestCsvFormatLoadSingleCsv:
    """Tests for load_single_csv function."""

    @pytest.fixture
    def tmpdir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_load_short_format(self, tmpdir):
        """Test loading CSV with short format column names."""
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        # Create test CSV with short format
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

        assert "ax_0_0" in result
        assert "ax_0_1" in result
        assert "trace1" in result["ax_0_0"]
        assert "trace2" in result["ax_0_1"]
        np.testing.assert_array_equal(result["ax_0_0"]["trace1"]["x"], [1, 2, 3])
        np.testing.assert_array_equal(result["ax_0_0"]["trace1"]["y"], [4, 5, 6])

    def test_load_legacy_format(self, tmpdir):
        """Test loading CSV with legacy format column names."""
        import pandas as pd

        from figrecipe._utils._numpy_io import load_single_csv

        # Create test CSV with legacy format
        df = pd.DataFrame(
            {
                "ax-row-0-col-0_trace-id-trace1_variable-x": [1, 2, 3],
                "ax-row-0-col-0_trace-id-trace1_variable-y": [4, 5, 6],
            }
        )
        csv_path = tmpdir / "legacy_format.csv"
        df.to_csv(csv_path, index=False)

        result = load_single_csv(csv_path)

        assert "ax_0_0" in result
        assert "trace1" in result["ax_0_0"]
        np.testing.assert_array_equal(result["ax_0_0"]["trace1"]["x"], [1, 2, 3])
        np.testing.assert_array_equal(result["ax_0_0"]["trace1"]["y"], [4, 5, 6])
