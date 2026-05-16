#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for CSV column support in declarative plot API."""

import numpy as np
import pytest


class TestResolveData:
    """Test resolve_data function for CSV column support."""

    def test_resolve_data_list(self):
        """Test resolve_data with inline list."""
        from figrecipe._api._plot_helpers import resolve_data

        result = resolve_data([1, 2, 3, 4])
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, [1, 2, 3, 4])

    def test_resolve_data_tuple(self):
        """Test resolve_data with tuple."""
        from figrecipe._api._plot_helpers import resolve_data

        result = resolve_data((1.0, 2.0, 3.0))
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, [1.0, 2.0, 3.0])

    def test_resolve_data_none(self):
        """Test resolve_data with None."""
        from figrecipe._api._plot_helpers import resolve_data

        result = resolve_data(None)
        assert result is None

    def test_resolve_data_csv_column(self, tmp_path):
        """Test resolve_data with CSV column name."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        # Create CSV file
        csv_path = tmp_path / "test_data.csv"
        csv_path.write_text("x,y,z\n1,10,100\n2,20,200\n3,30,300\n")

        clear_csv_cache()

        # Test column lookup
        result = resolve_data("y", data_file=str(csv_path))
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, [10, 20, 30])

    def test_resolve_data_csv_first_column(self, tmp_path):
        """Test resolve_data with first CSV column."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("time,value\n0.0,1.5\n1.0,2.5\n2.0,3.5\n")

        clear_csv_cache()

        result = resolve_data("time", data_file=str(csv_path))
        np.testing.assert_array_almost_equal(result, [0.0, 1.0, 2.0])

    def test_resolve_data_csv_last_column(self, tmp_path):
        """Test resolve_data with last CSV column."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")

        clear_csv_cache()

        result = resolve_data("c", data_file=str(csv_path))
        np.testing.assert_array_equal(result, [3, 6])

    def test_resolve_data_csv_invalid_column(self, tmp_path):
        """Test resolve_data with invalid column name."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("x,y\n1,2\n3,4\n")

        clear_csv_cache()

        with pytest.raises(ValueError, match="not found"):
            resolve_data("nonexistent", data_file=str(csv_path))

    def test_resolve_data_csv_with_spaces_in_values(self, tmp_path):
        """Test resolve_data with numeric CSV data."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("temp,pressure\n20.5,101.3\n21.0,101.2\n22.5,101.1\n")

        clear_csv_cache()

        temp = resolve_data("temp", data_file=str(csv_path))
        pressure = resolve_data("pressure", data_file=str(csv_path))

        np.testing.assert_array_almost_equal(temp, [20.5, 21.0, 22.5])
        np.testing.assert_array_almost_equal(pressure, [101.3, 101.2, 101.1])

    def test_resolve_data_npy_file(self, tmp_path):
        """Test resolve_data with .npy file."""
        from figrecipe._api._plot_helpers import resolve_data

        npy_path = tmp_path / "data.npy"
        data = np.array([1, 2, 3, 4, 5])
        np.save(npy_path, data)

        result = resolve_data(str(npy_path))
        np.testing.assert_array_equal(result, data)

    def test_resolve_data_passthrough(self):
        """Test resolve_data passes through numpy arrays."""
        from figrecipe._api._plot_helpers import resolve_data

        arr = np.array([1, 2, 3])
        result = resolve_data(arr)
        assert result is arr  # Should be same object


class TestCSVCache:
    """Test CSV caching functionality."""

    def test_csv_cache_reuse(self, tmp_path):
        """Test that CSV files are cached for reuse."""
        # _csv_cache lives in _data_resolver after refactor; _plot_helpers re-exports
        # clear_csv_cache and resolve_data but not the private cache dict itself
        from figrecipe._api._data_resolver import _csv_cache
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "cached.csv"
        csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")

        clear_csv_cache()
        assert len(_csv_cache) == 0

        # First access - should cache
        resolve_data("a", data_file=str(csv_path))
        assert len(_csv_cache) == 1

        # Second access - should use cache
        resolve_data("b", data_file=str(csv_path))
        assert len(_csv_cache) == 1  # Still just one entry

        # Third column - still cached
        resolve_data("c", data_file=str(csv_path))
        assert len(_csv_cache) == 1

    def test_clear_csv_cache(self, tmp_path):
        """Test clearing CSV cache."""
        from figrecipe._api._data_resolver import _csv_cache
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "test.csv"
        csv_path.write_text("x,y\n1,2\n")

        clear_csv_cache()
        resolve_data("x", data_file=str(csv_path))
        assert len(_csv_cache) == 1

        clear_csv_cache()
        assert len(_csv_cache) == 0

    def test_csv_cache_multiple_files(self, tmp_path):
        """Test caching multiple CSV files."""
        from figrecipe._api._data_resolver import _csv_cache
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv1 = tmp_path / "data1.csv"
        csv2 = tmp_path / "data2.csv"
        csv1.write_text("x,y\n1,2\n")
        csv2.write_text("a,b\n3,4\n")

        clear_csv_cache()

        resolve_data("x", data_file=str(csv1))
        resolve_data("a", data_file=str(csv2))

        assert len(_csv_cache) == 2


class TestPlotWithCSVColumns:
    """Test full plot creation with CSV column data."""

    def test_plot_scatter_from_csv(self, tmp_path):
        """Test creating scatter plot from CSV columns."""
        from figrecipe._api._plot import create_figure_from_spec
        from figrecipe._api._plot_helpers import clear_csv_cache

        # Create CSV
        csv_path = tmp_path / "experiment.csv"
        csv_path.write_text("time,temp,humidity\n0,20,50\n1,21,52\n2,22,55\n3,23,53\n")

        clear_csv_cache()

        spec = {
            "plots": [
                {
                    "type": "scatter",
                    "data_file": str(csv_path),
                    "x": "time",
                    "y": "temp",
                    "color": "blue",
                }
            ],
            "xlabel": "Time",
            "ylabel": "Temperature",
        }

        output_path = tmp_path / "scatter.png"
        result = create_figure_from_spec(spec, output_path=output_path)

        assert result["image_path"] == output_path
        assert output_path.exists()

    def test_plot_line_from_csv(self, tmp_path):
        """Test creating line plot from CSV columns."""
        from figrecipe._api._plot import create_figure_from_spec
        from figrecipe._api._plot_helpers import clear_csv_cache

        csv_path = tmp_path / "timeseries.csv"
        csv_path.write_text("x,y\n0,0\n1,1\n2,4\n3,9\n4,16\n")

        clear_csv_cache()

        spec = {
            "plots": [
                {
                    "type": "line",
                    "data_file": str(csv_path),
                    "x": "x",
                    "y": "y",
                    "label": "quadratic",
                }
            ],
            "legend": True,
        }

        output_path = tmp_path / "line.png"
        create_figure_from_spec(spec, output_path=output_path)
        assert output_path.exists()

    def test_plot_multiple_series_from_csv(self, tmp_path):
        """Test multiple plot series from same CSV file."""
        from figrecipe._api._plot import create_figure_from_spec
        from figrecipe._api._plot_helpers import clear_csv_cache

        csv_path = tmp_path / "multi.csv"
        csv_path.write_text("x,y1,y2\n0,1,2\n1,2,4\n2,3,6\n3,4,8\n")

        clear_csv_cache()

        spec = {
            "plots": [
                {
                    "type": "line",
                    "data_file": str(csv_path),
                    "x": "x",
                    "y": "y1",
                    "color": "blue",
                    "label": "Series 1",
                },
                {
                    "type": "line",
                    "data_file": str(csv_path),
                    "x": "x",
                    "y": "y2",
                    "color": "red",
                    "label": "Series 2",
                },
            ],
            "legend": True,
        }

        output_path = tmp_path / "multi_series.png"
        create_figure_from_spec(spec, output_path=output_path)
        assert output_path.exists()

    def test_plot_bar_from_csv(self, tmp_path):
        """Test bar plot from CSV columns."""
        from figrecipe._api._plot import create_figure_from_spec
        from figrecipe._api._plot_helpers import clear_csv_cache

        csv_path = tmp_path / "bar_data.csv"
        csv_path.write_text("category,value\n1,10\n2,25\n3,15\n4,30\n")

        clear_csv_cache()

        spec = {
            "plots": [
                {
                    "type": "bar",
                    "data_file": str(csv_path),
                    "x": "category",
                    "y": "value",
                }
            ],
        }

        output_path = tmp_path / "bar.png"
        create_figure_from_spec(spec, output_path=output_path)
        assert output_path.exists()

    def test_plot_mixed_csv_and_inline(self, tmp_path):
        """Test mixing CSV columns with inline data."""
        from figrecipe._api._plot import create_figure_from_spec
        from figrecipe._api._plot_helpers import clear_csv_cache

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("x,y\n0,0\n1,1\n2,2\n3,3\n")

        clear_csv_cache()

        spec = {
            "plots": [
                {
                    "type": "line",
                    "data_file": str(csv_path),
                    "x": "x",
                    "y": "y",
                    "label": "from CSV",
                },
                {
                    "type": "scatter",
                    "x": [0, 1, 2, 3],
                    "y": [0, 1, 4, 9],
                    "label": "inline data",
                },
            ],
            "legend": True,
        }

        output_path = tmp_path / "mixed.png"
        create_figure_from_spec(spec, output_path=output_path)
        assert output_path.exists()


class TestCSVEdgeCases:
    """Test edge cases for CSV column support."""

    def test_csv_single_row(self, tmp_path):
        """Test CSV with single data row."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "single.csv"
        csv_path.write_text("x,y\n42,99\n")

        clear_csv_cache()

        x = resolve_data("x", data_file=str(csv_path))
        y = resolve_data("y", data_file=str(csv_path))

        # Should handle single row gracefully
        assert len(x) >= 1
        assert len(y) >= 1

    def test_csv_with_integers(self, tmp_path):
        """Test CSV with integer values."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "integers.csv"
        csv_path.write_text("a,b\n1,2\n3,4\n5,6\n")

        clear_csv_cache()

        result = resolve_data("a", data_file=str(csv_path))
        np.testing.assert_array_equal(result, [1, 3, 5])

    def test_csv_with_floats(self, tmp_path):
        """Test CSV with float values."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "floats.csv"
        csv_path.write_text("val\n1.5\n2.5\n3.5\n")

        clear_csv_cache()

        result = resolve_data("val", data_file=str(csv_path))
        np.testing.assert_array_almost_equal(result, [1.5, 2.5, 3.5])

    def test_csv_column_case_sensitive(self, tmp_path):
        """Test that column names are case-sensitive."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        csv_path = tmp_path / "case.csv"
        csv_path.write_text("Name,name,NAME\n1,2,3\n")

        clear_csv_cache()

        # These should all be different columns
        result1 = resolve_data("Name", data_file=str(csv_path))
        result2 = resolve_data("name", data_file=str(csv_path))
        result3 = resolve_data("NAME", data_file=str(csv_path))

        np.testing.assert_array_equal(result1, [1])
        np.testing.assert_array_equal(result2, [2])
        np.testing.assert_array_equal(result3, [3])

    def test_csv_nonexistent_file(self, tmp_path):
        """Test error handling for nonexistent CSV file."""
        from figrecipe._api._plot_helpers import clear_csv_cache, resolve_data

        clear_csv_cache()

        nonexistent = str(tmp_path / "does_not_exist.csv")
        with pytest.raises(Exception):  # Could be FileNotFoundError or similar
            resolve_data("x", data_file=nonexistent)
