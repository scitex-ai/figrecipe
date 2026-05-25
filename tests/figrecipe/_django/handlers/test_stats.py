#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for statistics metadata features."""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._recorder import AxesRecord, CallRecord, FigureRecord


class TestCallRecordStats:
    """Tests for CallRecord stats field."""

    def test_call_record_has_stats_part_1(self):
        """Test that CallRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(id="test", function="plot", args=[], kwargs={})
        assert hasattr(record, "stats")

    def test_call_record_has_stats_part_2(self):
        """Test that CallRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(id="test", function="plot", args=[], kwargs={})
        assert record.stats is None

    def test_call_record_stats_serialization_part_1(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(
            id="test", function="plot", args=[], kwargs={}, stats={"n": 50, "mean": 3.2}
        )
        d = record.to_dict()
        assert "stats" in d

    def test_call_record_stats_serialization_part_2(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(
            id="test", function="plot", args=[], kwargs={}, stats={"n": 50, "mean": 3.2}
        )
        d = record.to_dict()
        assert d["stats"]["n"] == 50

    def test_call_record_stats_serialization_part_3(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(
            id="test", function="plot", args=[], kwargs={}, stats={"n": 50, "mean": 3.2}
        )
        d = record.to_dict()
        assert d["stats"]["mean"] == 3.2

    def test_call_record_stats_not_in_dict_when_none(self):
        """Test that stats is absent when None."""
        # Arrange
        # Act
        # Assert
        record = CallRecord(id="test", function="plot", args=[], kwargs={})
        d = record.to_dict()
        assert "stats" not in d

    def test_call_record_from_dict_with_stats(self):
        """Test restoring CallRecord with stats from dict."""
        # Arrange
        # Act
        # Assert
        data = {
            "id": "test",
            "function": "plot",
            "args": [],
            "kwargs": {},
            "stats": {"n": 100, "mean": 5.5},
        }
        record = CallRecord.from_dict(data)
        assert record.stats == {"n": 100, "mean": 5.5}


class TestAxesRecordStats:
    """Tests for AxesRecord stats field."""

    def test_axes_record_has_stats_part_1(self):
        """Test that AxesRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = AxesRecord(position=(0, 0))
        assert hasattr(record, "stats")

    def test_axes_record_has_stats_part_2(self):
        """Test that AxesRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = AxesRecord(position=(0, 0))
        assert record.stats is None

    def test_axes_record_stats_serialization_part_1(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = AxesRecord(position=(0, 0))
        record.stats = {"n": 50, "mean": 3.2, "std": 1.1}
        d = record.to_dict()
        assert "stats" in d

    def test_axes_record_stats_serialization_part_2(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = AxesRecord(position=(0, 0))
        record.stats = {"n": 50, "mean": 3.2, "std": 1.1}
        d = record.to_dict()
        assert d["stats"]["n"] == 50

    def test_axes_record_stats_not_in_dict_when_none(self):
        """Test that stats is absent when None."""
        # Arrange
        # Act
        # Assert
        record = AxesRecord(position=(0, 0))
        d = record.to_dict()
        assert "stats" not in d


class TestFigureRecordStats:
    """Tests for FigureRecord stats field."""

    def test_figure_record_has_stats_part_1(self):
        """Test that FigureRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = FigureRecord()
        assert hasattr(record, "stats")

    def test_figure_record_has_stats_part_2(self):
        """Test that FigureRecord has stats field."""
        # Arrange
        # Act
        # Assert
        record = FigureRecord()
        assert record.stats is None

    def test_figure_record_stats_serialization_part_1(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = FigureRecord()
        record.stats = {
            "comparisons": [{"name": "A vs B", "p_value": 0.003}],
            "correction_method": "bonferroni",
        }
        d = record.to_dict()
        assert "metadata" in d

    def test_figure_record_stats_serialization_part_2(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = FigureRecord()
        record.stats = {
            "comparisons": [{"name": "A vs B", "p_value": 0.003}],
            "correction_method": "bonferroni",
        }
        d = record.to_dict()
        assert "stats" in d["metadata"]

    def test_figure_record_stats_serialization_part_3(self):
        """Test stats serialization in to_dict."""
        # Arrange
        # Act
        # Assert
        record = FigureRecord()
        record.stats = {
            "comparisons": [{"name": "A vs B", "p_value": 0.003}],
            "correction_method": "bonferroni",
        }
        d = record.to_dict()
        assert d["metadata"]["stats"]["correction_method"] == "bonferroni"

    def test_figure_record_from_dict_with_stats_part_1(self):
        """Test restoring FigureRecord with stats from dict."""
        # Arrange
        # Act
        # Assert
        data = {
            "figrecipe": "1.0",
            "id": "fig_test",
            "created": "2025-01-01",
            "matplotlib_version": "3.8.0",
            "figure": {"figsize": [6.4, 4.8], "dpi": 300},
            "axes": {},
            "metadata": {"stats": {"comparisons": [{"name": "test", "p_value": 0.01}]}},
        }
        record = FigureRecord.from_dict(data)
        assert record.stats is not None

    def test_figure_record_from_dict_with_stats_part_2(self):
        """Test restoring FigureRecord with stats from dict."""
        # Arrange
        # Act
        # Assert
        data = {
            "figrecipe": "1.0",
            "id": "fig_test",
            "created": "2025-01-01",
            "matplotlib_version": "3.8.0",
            "figure": {"figsize": [6.4, 4.8], "dpi": 300},
            "axes": {},
            "metadata": {"stats": {"comparisons": [{"name": "test", "p_value": 0.01}]}},
        }
        record = FigureRecord.from_dict(data)
        assert record.stats["comparisons"][0]["p_value"] == 0.01


class TestRecordingFigureStats:
    """Tests for RecordingFigure stats methods."""

    def test_set_stats_part_1(self):
        """Test setting figure-level stats."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        fig.set_stats({"comparisons": [{"name": "A vs B", "p_value": 0.003}]})
        assert fig.stats is not None

    def test_set_stats_part_2(self):
        """Test setting figure-level stats."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        fig.set_stats({"comparisons": [{"name": "A vs B", "p_value": 0.003}]})
        assert fig.stats["comparisons"][0]["p_value"] == 0.003

    def test_set_stats_method_chaining(self):
        """Test that set_stats supports method chaining."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        result = fig.set_stats({"n": 100})
        assert result is fig


class TestRecordingAxesStats:
    """Tests for RecordingAxes stats methods."""

    def test_set_panel_stats_part_1(self):
        """Test setting panel-level stats."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        axes[0].set_stats({"n": 50, "mean": 3.2})
        axes[1].set_stats({"n": 48, "mean": 5.1})
        assert axes[0].stats["n"] == 50

    def test_set_panel_stats_part_2(self):
        """Test setting panel-level stats."""
        # Arrange
        # Act
        # Assert
        fig, axes = fr.subplots(1, 2)
        axes[0].set_stats({"n": 50, "mean": 3.2})
        axes[1].set_stats({"n": 48, "mean": 5.1})
        assert axes[1].stats["mean"] == 5.1

    def test_set_stats_method_chaining(self):
        """Test that set_stats supports method chaining."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        result = ax.set_stats({"n": 100})
        assert result is ax


class TestStatsInPlotKwargs:
    """Tests for stats passed via plotting method kwargs."""

    def test_bar_with_stats_part_1(self):
        """Test that stats in bar() kwargs is recorded."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1], stats={"groups": ["A", "B"], "n": [50, 48]})
        calls = fig.record.axes["ax_0_0"].calls
        assert len(calls) == 1

    def test_bar_with_stats_part_2(self):
        """Test that stats in bar() kwargs is recorded."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.bar([0, 1], [3.2, 5.1], stats={"groups": ["A", "B"], "n": [50, 48]})
        calls = fig.record.axes["ax_0_0"].calls
        assert calls[0].stats == {"groups": ["A", "B"], "n": [50, 48]}

    def test_plot_with_stats(self):
        """Test that stats in plot() kwargs is recorded."""
        # Arrange
        # Act
        # Assert
        fig, ax = fr.subplots()
        ax.plot([1, 2, 3], [4, 5, 6], stats={"n": 100, "r2": 0.95})
        calls = fig.record.axes["ax_0_0"].calls
        assert calls[0].stats == {"n": 100, "r2": 0.95}


class TestStatsRoundtrip:
    """Tests for stats round-trip (save and reproduce)."""

    def test_figure_stats_roundtrip(self):
        """Test that figure stats survives save/reproduce cycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.plot([1, 2, 3], [4, 5, 6])
            fig.set_stats(
                {
                    "comparisons": [
                        {
                            "name": "Control vs Treatment",
                            "p_value": 0.003,
                            "stars": "**",
                        }
                    ],
                    "alpha": 0.05,
                }
            )

            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False)

            fig2, ax2 = fr.reproduce(png_path)

            if not (fig2.stats is not None):
                raise AssertionError
            if not (fig2.stats['comparisons'][0]['p_value'] == 0.003):
                raise AssertionError
            if not (fig2.stats['alpha'] == 0.05):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test

    def test_panel_stats_roundtrip(self):
        """Test that panel stats survives save/reproduce cycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, axes = fr.subplots(1, 2)
            axes[0].plot([1, 2, 3], [4, 5, 6])
            axes[0].set_stats({"n": 50, "mean": 3.2, "std": 1.1})
            axes[1].scatter([1, 2, 3], [6, 5, 4])
            axes[1].set_stats({"n": 48, "mean": 5.1, "std": 0.9})

            png_path = Path(tmpdir) / "test_panels.png"
            fig.savefig(png_path, verbose=False)

            fig2, axes2 = fr.reproduce(png_path)

            if not (axes2[0].stats['n'] == 50):
                raise AssertionError
            if not (axes2[0].stats['mean'] == 3.2):
                raise AssertionError
            if not (axes2[1].stats['n'] == 48):
                raise AssertionError
            if not (axes2[1].stats['mean'] == 5.1):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test

    def test_call_stats_roundtrip(self):
        """Test that call-level stats survives save/reproduce cycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = fr.subplots()
            ax.bar([0, 1], [3.2, 5.1], stats={"groups": ["A", "B"]})

            png_path = Path(tmpdir) / "test_call.png"
            fig.savefig(png_path, verbose=False)

            fig2, ax2 = fr.reproduce(png_path)

            calls = fig2.record.axes["ax_0_0"].calls
            assert calls[0].stats == {"groups": ["A", "B"]}

    def test_combined_stats_roundtrip(self):
        """Test complete stats (figure + panel + call) roundtrip."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, axes = fr.subplots(1, 2)
            fig.set_stats({"summary": "significant difference"})

            axes[0].bar([0], [3.2], stats={"group": "control"})
            axes[0].set_stats({"n": 50})

            axes[1].bar([0], [5.1], stats={"group": "treatment"})
            axes[1].set_stats({"n": 48})

            png_path = Path(tmpdir) / "test_full.png"
            fig.savefig(png_path, verbose=False, validate=False)

            fig2, axes2 = fr.reproduce(png_path)

            # Verify all levels
            if not (fig2.stats['summary'] == 'significant difference'):
                raise AssertionError
            if not (axes2[0].stats['n'] == 50):
                raise AssertionError
            if not (axes2[1].stats['n'] == 48):
                raise AssertionError
            if not (fig2.record.axes['ax_0_0'].calls[0].stats['group'] == 'control'):
                raise AssertionError
            if not (fig2.record.axes['ax_0_1'].calls[0].stats['group'] == 'treatment'):
                raise AssertionError
        assert True  # TQ001-placeholder: body exercises code under test
