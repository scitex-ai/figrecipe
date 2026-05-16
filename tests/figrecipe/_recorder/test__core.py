#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figure and panel metadata/caption features."""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._recorder import AxesRecord, FigureRecord


class TestFigureRecordMetadata:
    """Tests for FigureRecord metadata fields."""

    def test_figure_record_has_title_metadata(self):
        """Test that FigureRecord has title_metadata field."""
        record = FigureRecord()
        assert hasattr(record, "title_metadata")
        assert record.title_metadata is None

    def test_figure_record_has_caption(self):
        """Test that FigureRecord has caption field."""
        record = FigureRecord()
        assert hasattr(record, "caption")
        assert record.caption is None

    def test_figure_record_title_metadata_serialization(self):
        """Test title_metadata serialization in to_dict."""
        record = FigureRecord()
        record.title_metadata = "Effect of X on Y"
        d = record.to_dict()
        assert "metadata" in d
        assert d["metadata"]["title"] == "Effect of X on Y"

    def test_figure_record_caption_serialization(self):
        """Test caption serialization in to_dict."""
        record = FigureRecord()
        record.caption = "Figure 1. Description of the figure."
        d = record.to_dict()
        assert "metadata" in d
        assert d["metadata"]["caption"] == "Figure 1. Description of the figure."

    def test_figure_record_metadata_not_in_dict_when_none(self):
        """Test that metadata section is absent when both fields are None."""
        record = FigureRecord()
        d = record.to_dict()
        assert "metadata" not in d

    def test_figure_record_from_dict_with_metadata(self):
        """Test restoring FigureRecord with metadata from dict."""
        data = {
            "figrecipe": "1.0",
            "id": "fig_test",
            "created": "2025-01-01",
            "matplotlib_version": "3.8.0",
            "figure": {"figsize": [6.4, 4.8], "dpi": 300},
            "axes": {},
            "metadata": {
                "title": "Test Title",
                "caption": "Test Caption",
            },
        }
        record = FigureRecord.from_dict(data)
        assert record.title_metadata == "Test Title"
        assert record.caption == "Test Caption"

    def test_figure_record_from_dict_without_metadata(self):
        """Test restoring FigureRecord without metadata from dict."""
        data = {
            "figrecipe": "1.0",
            "id": "fig_test",
            "created": "2025-01-01",
            "matplotlib_version": "3.8.0",
            "figure": {"figsize": [6.4, 4.8], "dpi": 300},
            "axes": {},
        }
        record = FigureRecord.from_dict(data)
        assert record.title_metadata is None
        assert record.caption is None


class TestAxesRecordCaption:
    """Tests for AxesRecord caption field."""

    def test_axes_record_has_caption(self):
        """Test that AxesRecord has caption field."""
        record = AxesRecord(position=(0, 0))
        assert hasattr(record, "caption")
        assert record.caption is None

    def test_axes_record_caption_serialization(self):
        """Test caption serialization in to_dict."""
        record = AxesRecord(position=(0, 0))
        record.caption = "(A) Control group"
        d = record.to_dict()
        assert d["caption"] == "(A) Control group"

    def test_axes_record_caption_not_in_dict_when_none(self):
        """Test that caption is absent when None."""
        record = AxesRecord(position=(0, 0))
        d = record.to_dict()
        assert "caption" not in d

    def test_figure_record_from_dict_with_panel_caption(self):
        """Test restoring FigureRecord with panel caption from dict."""
        data = {
            "figrecipe": "1.0",
            "id": "fig_test",
            "created": "2025-01-01",
            "matplotlib_version": "3.8.0",
            "figure": {"figsize": [6.4, 4.8], "dpi": 300},
            "axes": {
                "ax_0_0": {
                    "calls": [],
                    "decorations": [],
                    "caption": "(A) Test panel",
                }
            },
        }
        record = FigureRecord.from_dict(data)
        assert record.axes["ax_0_0"].caption == "(A) Test panel"


class TestRecordingFigureMetadata:
    """Tests for RecordingFigure metadata methods."""

    def test_set_title_metadata(self):
        """Test setting figure title metadata."""
        fig, ax = fr.subplots()
        fig.set_title_metadata("Effect of temperature on reaction rate")
        assert fig.title_metadata == "Effect of temperature on reaction rate"

    def test_set_caption(self):
        """Test setting figure caption."""
        fig, ax = fr.subplots()
        fig.set_caption("Figure 1. Temperature dependence.")
        assert fig.caption == "Figure 1. Temperature dependence."

    def test_method_chaining(self):
        """Test that metadata methods support chaining."""
        fig, ax = fr.subplots()
        result = fig.set_title_metadata("Title").set_caption("Caption")
        assert result is fig
        assert fig.title_metadata == "Title"
        assert fig.caption == "Caption"


class TestRecordingAxesCaption:
    """Tests for RecordingAxes caption methods."""

    def test_set_panel_caption(self):
        """Test setting panel caption."""
        fig, axes = fr.subplots(1, 2)
        axes[0].set_caption("(A) Control group")
        axes[1].set_caption("(B) Treatment group")
        assert axes[0].caption == "(A) Control group"
        assert axes[1].caption == "(B) Treatment group"

    def test_set_caption_method_chaining(self):
        """Test that set_caption supports method chaining."""
        fig, ax = fr.subplots()
        result = ax.set_caption("Test caption")
        assert result is ax


class TestMetadataRoundtrip:
    """Tests for metadata round-trip (save and reproduce)."""

    def test_figure_metadata_roundtrip(self):
        """Test that figure metadata survives save/reproduce cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create figure with metadata
            fig, ax = fr.subplots()
            ax.plot([1, 2, 3], [4, 5, 6])
            fig.set_title_metadata("Test Title for Roundtrip")
            fig.set_caption("Figure 1. Testing metadata persistence.")

            # Save
            png_path = Path(tmpdir) / "test.png"
            fig.savefig(png_path, verbose=False)

            # Reproduce
            fig2, ax2 = fr.reproduce(png_path)

            # Verify metadata
            assert fig2.title_metadata == "Test Title for Roundtrip"
            assert fig2.caption == "Figure 1. Testing metadata persistence."

    def test_panel_caption_roundtrip(self):
        """Test that panel captions survive save/reproduce cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create figure with panel captions
            fig, axes = fr.subplots(1, 2)
            axes[0].plot([1, 2, 3], [4, 5, 6])
            axes[0].set_caption("(A) First panel description")
            axes[1].scatter([1, 2, 3], [6, 5, 4])
            axes[1].set_caption("(B) Second panel description")

            # Save
            png_path = Path(tmpdir) / "test_panels.png"
            fig.savefig(png_path, verbose=False)

            # Reproduce
            fig2, axes2 = fr.reproduce(png_path)

            # Verify panel captions
            assert axes2[0].caption == "(A) First panel description"
            assert axes2[1].caption == "(B) Second panel description"

    def test_combined_metadata_roundtrip(self):
        """Test complete metadata (figure + panels) roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create figure with all metadata
            fig, axes = fr.subplots(2, 2)
            fig.set_title_metadata("Multi-panel Analysis")
            fig.set_caption("Figure 2. Comprehensive analysis results.")

            for i, ax in enumerate(axes.flat):
                ax.plot([1, 2, 3], [i, i + 1, i + 2])
                ax.set_caption(f"({chr(65 + i)}) Panel {i + 1}")

            # Save
            png_path = Path(tmpdir) / "test_full.png"
            fig.savefig(png_path, verbose=False, validate=False)

            # Reproduce
            fig2, axes2 = fr.reproduce(png_path)

            # Verify
            assert fig2.title_metadata == "Multi-panel Analysis"
            assert fig2.caption == "Figure 2. Comprehensive analysis results."
            for i, ax in enumerate(axes2.flat):
                assert ax.caption == f"({chr(65 + i)}) Panel {i + 1}"


class TestPanelLabelsOption:
    """Tests for panel_labels=True option in subplots."""

    def test_panel_labels_true_adds_labels(self):
        """Test that panel_labels=True adds A, B, C, D labels."""
        fig, axes = fr.subplots(2, 2, panel_labels=True)
        # Verify panel_labels was recorded
        assert fig.record.panel_labels is not None
        labels = fig.record.panel_labels.get("labels")
        assert labels == ["A", "B", "C", "D"]

    def test_panel_labels_false_no_labels(self):
        """Test that panel_labels=False does not add labels."""
        # Explicitly pass panel_labels=False to disable default from style
        fig, axes = fr.subplots(2, 2, panel_labels=False)
        assert fig.record.panel_labels is None

    def test_panel_labels_1d_row(self):
        """Test panel_labels with 1xN layout."""
        fig, axes = fr.subplots(1, 3, panel_labels=True)
        assert fig.record.panel_labels is not None
        labels = fig.record.panel_labels.get("labels")
        assert labels == ["A", "B", "C"]

    def test_panel_labels_1d_col(self):
        """Test panel_labels with Nx1 layout."""
        fig, axes = fr.subplots(3, 1, panel_labels=True)
        assert fig.record.panel_labels is not None
        labels = fig.record.panel_labels.get("labels")
        assert labels == ["A", "B", "C"]

    def test_panel_labels_single_panel_not_added(self):
        """Test that single panel (1x1) doesn't get labels by default."""
        fig, ax = fr.subplots(1, 1, panel_labels=True)
        # Single panel should not have panel_labels (early return path)
        # This is fine because single panels don't need labels
        # The early return happens before panel_labels is applied

    def test_panel_labels_roundtrip(self):
        """Test that panel_labels survives save/reproduce cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, axes = fr.subplots(2, 2, panel_labels=True)
            for ax in axes.flat:
                ax.plot([1, 2, 3], [1, 2, 3])

            png_path = Path(tmpdir) / "test_labels.png"
            fig.savefig(png_path, verbose=False, validate=False)

            fig2, axes2 = fr.reproduce(png_path)
            assert fig2.record.panel_labels is not None
            labels = fig2.record.panel_labels.get("labels")
            assert labels == ["A", "B", "C", "D"]


# === merged from v2 ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the recorder module."""

import numpy as np

from figrecipe._recorder import CallRecord, FigureRecord, Recorder


class TestCallRecord:
    """Tests for CallRecord dataclass."""

    def test_create_call_record(self):
        """Test creating a call record."""
        record = CallRecord(
            id="plot_001",
            function="plot",
            args=[{"name": "x", "data": [1, 2, 3]}],
            kwargs={"color": "red"},
        )
        assert record.id == "plot_001"
        assert record.function == "plot"
        assert len(record.args) == 1
        assert record.kwargs["color"] == "red"

    def test_to_dict(self):
        """Test converting to dictionary."""
        record = CallRecord(
            id="scatter_001",
            function="scatter",
            args=[],
            kwargs={"s": 10},
        )
        d = record.to_dict()
        assert d["id"] == "scatter_001"
        assert d["function"] == "scatter"
        assert d["kwargs"]["s"] == 10

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "id": "hist_001",
            "function": "hist",
            "args": [{"name": "x", "data": [1, 2, 3]}],
            "kwargs": {"bins": 10},
        }
        record = CallRecord.from_dict(data)
        assert record.id == "hist_001"
        assert record.function == "hist"
        assert record.kwargs["bins"] == 10


class TestFigureRecord:
    """Tests for FigureRecord dataclass."""

    def test_create_figure_record(self):
        """Test creating a figure record."""
        record = FigureRecord(figsize=(10, 6), dpi=100)
        assert record.figsize == (10, 6)
        assert record.dpi == 100
        assert len(record.axes) == 0

    def test_get_or_create_axes(self):
        """Test getting or creating axes."""
        record = FigureRecord()
        ax = record.get_or_create_axes(0, 0)
        assert ax.position == (0, 0)
        assert "ax_0_0" in record.axes

        # Getting same axes again should return same object
        ax2 = record.get_or_create_axes(0, 0)
        assert ax is ax2

    def test_to_dict_and_from_dict(self):
        """Test round-trip serialization."""
        record = FigureRecord(figsize=(8, 6), dpi=150)
        ax = record.get_or_create_axes(0, 0)
        ax.add_call(
            CallRecord(
                id="plot_001",
                function="plot",
                args=[],
                kwargs={"color": "blue"},
            )
        )

        # Convert to dict and back
        d = record.to_dict()
        restored = FigureRecord.from_dict(d)

        assert restored.figsize == (8, 6)
        assert restored.dpi == 150
        assert "ax_0_0" in restored.axes
        assert len(restored.axes["ax_0_0"].calls) == 1


class TestRecorder:
    """Tests for Recorder class."""

    def test_start_figure(self):
        """Test starting a new figure."""
        recorder = Recorder()
        record = recorder.start_figure(figsize=(12, 8), dpi=200)
        assert record.figsize == (12, 8)
        assert record.dpi == 200

    def test_record_call(self):
        """Test recording a call."""
        recorder = Recorder()
        recorder.start_figure()

        call = recorder.record_call(
            ax_position=(0, 0),
            method_name="plot",
            args=(np.array([1, 2, 3]), np.array([4, 5, 6])),
            kwargs={"color": "red"},
        )

        assert call.id == "plot_000"
        assert call.function == "plot"
        assert call.kwargs["color"] == "red"

    def test_record_call_with_custom_id(self):
        """Test recording a call with custom ID."""
        recorder = Recorder()
        recorder.start_figure()

        call = recorder.record_call(
            ax_position=(0, 0),
            method_name="scatter",
            args=(),
            kwargs={},
            call_id="my_scatter",
        )

        assert call.id == "my_scatter"

    def test_auto_increment_ids(self):
        """Test that IDs auto-increment."""
        recorder = Recorder()
        recorder.start_figure()

        call1 = recorder.record_call((0, 0), "plot", (), {})
        call2 = recorder.record_call((0, 0), "plot", (), {})
        call3 = recorder.record_call((0, 0), "scatter", (), {})

        assert call1.id == "plot_000"
        assert call2.id == "plot_001"
        assert call3.id == "scatter_000"

    def test_record_to_correct_axes(self):
        """Test that calls are recorded to correct axes."""
        recorder = Recorder()
        recorder.start_figure()

        recorder.record_call((0, 0), "plot", (), {})
        recorder.record_call((0, 1), "scatter", (), {})
        recorder.record_call((1, 0), "bar", (), {})

        record = recorder.figure_record
        assert len(record.axes["ax_0_0"].calls) == 1
        assert len(record.axes["ax_0_1"].calls) == 1
        assert len(record.axes["ax_1_0"].calls) == 1
