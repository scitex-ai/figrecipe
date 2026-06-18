#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for TILED (row-justified, whitespace-free) composition.

The tiled mode (``fr.compose(layout=[["A","B","C"],["D"]], sources=...)``)
gives every panel its true aspect ratio, makes every panel in a row share one
height edge-to-edge (no intra-row whitespace), and makes every row span the
same width (no ragged right edge). The first layout row is rendered on top.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._composition._tile import build_tiled_sources

# Tolerance for floating-point geometry comparisons (mm).
TOL = 1e-6


def _make_panel(tmp_path, name, figsize):
    """Save a single-panel recipe with a distinct aspect ratio."""
    fig, ax = fr.subplots(figsize=figsize)
    ax.plot([1, 2, 3], [1, 4, 9], id=name)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    path = tmp_path / f"{name}.yaml"
    fr.save(fig, path, validate=False, verbose=False)
    return path


@pytest.fixture
def four_panels(tmp_path):
    """Four saved panels with distinct aspect ratios (A wide, B square, C tall, D very-wide)."""
    return {
        "A": _make_panel(tmp_path, "A", (3, 2)),
        "B": _make_panel(tmp_path, "B", (2, 2)),
        "C": _make_panel(tmp_path, "C", (2, 3)),
        "D": _make_panel(tmp_path, "D", (5, 2)),
    }


class TestTiledRoundTrip:
    """|A B C| / |D| composes and survives save/reproduce."""

    def test_roundtrips_no_not_reproduced_artifact(self, tmp_path, four_panels):
        """fr.save validates with no <stem>-not-reproduced.png left behind."""
        # Arrange
        fig, axes = fr.compose(
            layout=[["A", "B", "C"], ["D"]],
            sources=four_panels,
            width_mm=180,
            gap_mm=1.0,
        )
        out = tmp_path / "composed.png"
        # Act
        fr.save(fig, out, verbose=False)
        # Assert
        assert not (tmp_path / "composed-not-reproduced.png").exists()


class TestTiledNoWhitespace:
    """Every row spans the full width W (no ragged edge)."""

    def test_every_row_spans_full_width(self, four_panels):
        """sum(row panel widths) + (k-1)*gap == W for EVERY row (incl. row 2 = D)."""
        # Arrange
        gap = 1.0
        rows = [["A", "B", "C"], ["D"]]
        # Act
        sources_mm, (W, _h) = build_tiled_sources(
            rows, four_panels, width_mm=180, gap_mm=gap
        )
        row_spans = [
            sum(sources_mm[four_panels[lab]]["size_mm"][0] for lab in row)
            + (len(row) - 1) * gap
            for row in rows
        ]
        # Assert
        assert all(abs(span - W) < TOL for span in row_spans)


class TestTiledEqualRowHeight:
    """Within a row all panels share one common height."""

    def test_row_panels_share_height(self, four_panels):
        """The three top-row panels (A, B, C) all get the same panel height."""
        # Arrange
        rows = [["A", "B", "C"], ["D"]]
        # Act
        sources_mm, _canvas = build_tiled_sources(
            rows, four_panels, width_mm=180, gap_mm=1.0
        )
        heights = [sources_mm[four_panels[lab]]["size_mm"][1] for lab in rows[0]]
        # Assert
        assert max(heights) - min(heights) < TOL


class TestTiledEdgeToEdge:
    """With gap_mm=0 adjacent panels in a row share an x-edge."""

    def test_adjacent_panels_share_edge(self, four_panels):
        """next.x0 == prev.x1 for consecutive top-row panels when gap_mm=0."""
        # Arrange
        rows = [["A", "B", "C"], ["D"]]
        # Act
        sources_mm, _canvas = build_tiled_sources(
            rows, four_panels, width_mm=180, gap_mm=0.0
        )
        placed = [
            (
                sources_mm[four_panels[lab]]["xy_mm"][0],
                sources_mm[four_panels[lab]]["size_mm"][0],
            )
            for lab in rows[0]
        ]
        placed.sort()
        gaps = [
            placed[i + 1][0] - (placed[i][0] + placed[i][1])
            for i in range(len(placed) - 1)
        ]
        # Assert
        assert all(abs(g) < TOL for g in gaps)


class TestTiledFirstRowOnTop:
    """The first layout row is rendered visually on top (smallest y_mm)."""

    def test_first_row_has_smallest_y(self, four_panels):
        """Row-1 panels get y_mm=0 while row-2 (D) gets a larger y_mm (top-down origin)."""
        # Arrange
        rows = [["A", "B", "C"], ["D"]]
        # Act
        sources_mm, _canvas = build_tiled_sources(
            rows, four_panels, width_mm=180, gap_mm=1.0
        )
        top_y = max(sources_mm[four_panels[lab]]["xy_mm"][1] for lab in rows[0])
        d_y = sources_mm[four_panels["D"]]["xy_mm"][1]
        # Assert
        assert top_y < d_y


class TestTiledStringLayout:
    """A multiline-string layout equals the list-of-lists layout."""

    def test_string_layout_matches_list_layout(self, four_panels):
        """'A B C\\nD' produces the same geometry as [["A","B","C"],["D"]]."""
        # Arrange
        list_mm, list_canvas = build_tiled_sources(
            [["A", "B", "C"], ["D"]], four_panels, width_mm=180, gap_mm=1.0
        )
        # Act
        str_mm, str_canvas = build_tiled_sources(
            "A B C\nD", four_panels, width_mm=180, gap_mm=1.0
        )
        # Assert
        assert str_mm == list_mm and str_canvas == list_canvas


class TestTiledValidation:
    """Label/source mismatches fail loud."""

    def test_missing_source_raises(self, four_panels):
        """A layout label with no matching source raises ValueError."""
        # Arrange
        bad_layout = [["A", "B", "C"], ["Z"]]  # Z has no source
        # Act
        # Assert
        with pytest.raises(ValueError):
            build_tiled_sources(bad_layout, four_panels, width_mm=180, gap_mm=1.0)


# EOF
