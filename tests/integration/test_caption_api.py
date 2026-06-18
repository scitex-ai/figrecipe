#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for the figrecipe caption API.

Exercises the real public surface end-to-end (fr.subplots(caption=),
fr.compose(caption=, panel_captions=), fr.add_figure_caption,
fr.add_panel_captions, fr.panel_label) plus FigureRecord caption
round-trip. No mocks — every test runs against the real objects.
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as _plt  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._recorder import FigureRecord  # noqa: E402


def _save_minimal_source(tmpdir):
    """Save a one-line recipe and return its path (shared compose arrange)."""
    fig_base, ax_base = fr.subplots()
    ax_base.plot([1, 2, 3], [1, 4, 9], id="line1")
    src_path = os.path.join(tmpdir, "src.yaml")
    fr.save(fig_base, src_path, validate=False, verbose=False)
    _plt.close(fig_base)
    return src_path


def test_subplots_without_caption_returns_figure():
    # Arrange
    # Act
    fig, axes = fr.subplots()
    # Assert
    assert fig is not None
    _plt.close(fig)


def test_subplots_without_caption_returns_axes():
    # Arrange
    # Act
    fig, axes = fr.subplots()
    # Assert
    assert axes is not None
    _plt.close(fig)


def test_subplots_with_caption_records_caption_text():
    # Arrange
    # Act
    fig, axes = fr.subplots(caption="Test caption text")
    # Assert
    assert fig.record.caption == "Test caption text"
    _plt.close(fig)


def test_subplots_caption_appends_figure_text_entry():
    # Arrange
    # Act
    fig, axes = fr.subplots(caption="Persist me")
    # Assert
    assert len(fig.record.figure_texts) > 0
    _plt.close(fig)


def test_subplots_caption_none_returns_figure():
    # Arrange
    # Act
    fig, axes = fr.subplots(caption=None)
    # Assert
    assert fig is not None
    _plt.close(fig)


def test_compose_with_figure_caption_records_caption(tmp_path):
    # Arrange
    src_path = _save_minimal_source(str(tmp_path))
    # Act
    fig, axes = fr.compose(
        layout=(1, 1),
        sources={(0, 0): src_path},
        caption="Composed figure caption",
    )
    # Assert
    assert fig.record.caption == "Composed figure caption"
    _plt.close(fig)


def test_compose_with_panel_captions_records_main_caption(tmp_path):
    # Arrange
    src_path = _save_minimal_source(str(tmp_path))
    # Act
    fig, axes = fr.compose(
        layout=(1, 2),
        sources={(0, 0): src_path, (0, 1): src_path},
        caption="Panel caption figure",
        panel_captions=["Panel A", "Panel B"],
    )
    # Assert
    assert fig.record.caption == "Panel caption figure"
    _plt.close(fig)


def test_compose_with_panel_captions_stores_panel_list(tmp_path):
    # Arrange
    src_path = _save_minimal_source(str(tmp_path))
    # Act
    fig, axes = fr.compose(
        layout=(1, 2),
        sources={(0, 0): src_path, (0, 1): src_path},
        caption="Panel caption figure",
        panel_captions=["Panel A", "Panel B"],
    )
    # Assert
    assert fig.record.figure_panel_captions == ["Panel A", "Panel B"]
    _plt.close(fig)


def test_public_api_exposes_add_figure_caption():
    # Arrange
    # Act
    fn = fr.add_figure_caption
    # Assert
    assert callable(fn)


def test_public_api_exposes_add_panel_captions():
    # Arrange
    # Act
    fn = fr.add_panel_captions
    # Assert
    assert callable(fn)


def test_public_api_exposes_panel_label_helper():
    # Arrange
    # Act
    fn = fr.panel_label
    # Assert
    assert callable(fn)


def test_add_figure_caption_strips_markdown_markers():
    # Arrange
    fig, ax = _plt.subplots()
    # Act
    result = fr.add_figure_caption(fig, "**Bold** and *italic*")
    # Assert
    assert "*" not in result
    _plt.close(fig)


def test_panel_label_on_recording_axes_does_not_raise():
    # Arrange
    fig, axes = fr.subplots()
    ax = axes if hasattr(axes, "text") else axes[0]
    completed = False
    # Act
    fr.panel_label(ax, "A")
    completed = True
    # Assert
    assert completed
    _plt.close(fig)


def test_figure_record_serializes_panel_captions_to_dict():
    # Arrange
    record = FigureRecord()
    record.figure_panel_captions = ["A caption", "B caption"]
    # Act
    d = record.to_dict()
    # Assert
    assert d["figure"]["panel_captions"] == ["A caption", "B caption"]


def test_figure_record_deserializes_panel_captions_from_dict():
    # Arrange
    d = {"figure": {"panel_captions": ["capt1", "capt2"]}}
    # Act
    record = FigureRecord.from_dict(d)
    # Assert
    assert record.figure_panel_captions == ["capt1", "capt2"]


def test_compose_panel_captions_reproduce(tmp_path):
    # Per-panel compose captions were rendered live via raw mpl_fig.text and
    # dropped on reproduce (only the figure-level caption round-tripped). They
    # are now recorded as figure_texts; this guards that a reproduced composed
    # figure shows its per-panel caption text.
    # Arrange
    src_path = _save_minimal_source(str(tmp_path))
    fig, _axes = fr.compose(
        layout=(1, 2),
        sources={(0, 0): src_path, (0, 1): src_path},
        panel_captions=["Alpha caption", "Beta caption"],
    )
    composed = os.path.join(str(tmp_path), "composed.yaml")
    fr.save(fig, composed, validate=False, verbose=False)
    _plt.close(fig)
    # Act
    rfig, _ = fr.reproduce(composed)
    mpl_fig = rfig.fig if hasattr(rfig, "fig") else rfig
    repro_texts = [t.get_text() for t in mpl_fig.texts]
    # Assert
    assert any("Alpha caption" in t for t in repro_texts)
