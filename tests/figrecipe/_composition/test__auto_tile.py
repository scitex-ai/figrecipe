#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the auto-tiler (aspect-ratio bin-packing for tight tiling).

``auto_tile_layout(aspects, width_mm, height_mm=None, gap_mm=1.0)`` decides
how many rows to use and which labels go in which row, then sizes every
panel with the SAME row-height formula ``build_tiled_sources`` uses -- it
never stretches a panel, it only proposes a ``layout`` + ``sizes_mm`` that
panels should be RE-AUTHORED at.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._composition._auto_tile import auto_tile_layout
from figrecipe._composition._tile import _source_aspect, build_tiled_sources

# Tolerance for floating-point aspect-ratio comparisons.
TOL = 1e-6


def _make_panel(tmp_path, name, figsize):
    """Save a single-panel recipe with a distinct aspect ratio (no mocks)."""
    fig, ax = fr.subplots(figsize=figsize)
    ax.plot([1, 2, 3], [1, 4, 9], id=name)
    path = tmp_path / f"{name}.yaml"
    fr.save(fig, path, validate=False, verbose=False)
    return path


class TestAutoTileWidthOnly:
    """width_mm only (no height_mm): a valid row-list covering every label once."""

    def test_layout_is_a_list_of_lists(self):
        # Arrange: four panels with mixed aspect ratios.
        aspects = {"A": 3.0 / 2.0, "B": 1.0, "C": 2.0 / 3.0, "D": 5.0 / 2.0}
        # Act
        layout, _sizes_mm, _canvas = auto_tile_layout(aspects, width_mm=180)
        # Assert: row-list format.
        assert isinstance(layout, list) and all(isinstance(row, list) for row in layout)

    def test_layout_covers_every_label_exactly_once(self):
        # Arrange: four panels with mixed aspect ratios.
        aspects = {"A": 3.0 / 2.0, "B": 1.0, "C": 2.0 / 3.0, "D": 5.0 / 2.0}
        # Act
        layout, _sizes_mm, _canvas = auto_tile_layout(aspects, width_mm=180)
        placed = [lab for row in layout for lab in row]
        # Assert: every label placed exactly once, no duplicates.
        assert sorted(placed) == sorted(aspects.keys()) and len(placed) == len(
            set(placed)
        )

    def test_sizes_mm_covers_every_label(self):
        # Arrange: four panels with mixed aspect ratios.
        aspects = {"A": 3.0 / 2.0, "B": 1.0, "C": 2.0 / 3.0, "D": 5.0 / 2.0}
        # Act
        _layout, sizes_mm, _canvas = auto_tile_layout(aspects, width_mm=180)
        # Assert
        assert set(sizes_mm.keys()) == set(aspects.keys())

    def test_panel_aspect_ratio_is_preserved_not_stretched(self):
        # Arrange
        aspects = {"A": 3.0 / 2.0, "B": 1.0, "C": 2.0 / 3.0, "D": 5.0 / 2.0}
        # Act
        _layout, sizes_mm, _canvas = auto_tile_layout(aspects, width_mm=180)
        # Assert: w/h in sizes_mm matches the input aspect exactly (no stretch).
        for label, (w_mm, h_mm) in sizes_mm.items():
            assert abs((w_mm / h_mm) - aspects[label]) < TOL


class TestAutoTileWithHeightTarget:
    """height_mm given: packer searches row-counts to approach the target height."""

    def test_total_height_close_to_requested(self):
        # Arrange: six panels, ask for a specific canvas height.
        aspects = {
            "A": 3.0 / 2.0,
            "B": 1.0,
            "C": 2.0 / 3.0,
            "D": 5.0 / 2.0,
            "E": 1.5,
            "F": 0.8,
        }
        target_height_mm = 120.0
        # Act
        _layout, _sizes_mm, (_w, total_height_mm) = auto_tile_layout(
            aspects, width_mm=180, height_mm=target_height_mm
        )
        # Assert: row-count is a DISCRETE search (1..N rows), so exact match is
        # not expected -- 25% of the target is a generous but meaningful bound
        # that still catches a badly-packed (e.g. all-one-row or all-N-rows)
        # regression.
        assert abs(total_height_mm - target_height_mm) < 0.25 * target_height_mm


class TestAutoTileSinglePanel:
    """N=1 degenerate case: one row, full width, height derived from aspect."""

    def test_single_panel_is_one_row(self):
        # Arrange
        aspect = 4.0 / 3.0
        width_mm = 100.0
        # Act
        layout, _sizes_mm, _canvas_mm = auto_tile_layout(
            {"A": aspect}, width_mm=width_mm
        )
        # Assert
        assert layout == [["A"]]

    def test_single_panel_size_fills_width_at_true_aspect(self):
        # Arrange
        aspect = 4.0 / 3.0
        width_mm = 100.0
        # Act
        _layout, sizes_mm, _canvas_mm = auto_tile_layout(
            {"A": aspect}, width_mm=width_mm
        )
        # Assert
        assert sizes_mm["A"] == pytest.approx((width_mm, width_mm / aspect))

    def test_single_panel_canvas_matches_panel_size(self):
        # Arrange
        aspect = 4.0 / 3.0
        width_mm = 100.0
        # Act
        _layout, _sizes_mm, canvas_mm = auto_tile_layout(
            {"A": aspect}, width_mm=width_mm
        )
        # Assert
        assert canvas_mm == pytest.approx((width_mm, width_mm / aspect))


class TestAutoTileMatchesBuildTiledSources:
    """DRY-verification: auto_tile_layout's sizes match build_tiled_sources's.

    Feeds the auto-tiler's proposed ``layout`` into the REAL
    ``build_tiled_sources`` (real saved panels, no mocks) and checks the
    resulting geometry is IDENTICAL -- proving both call the same shared
    row-height formula rather than two independently drifting ones.
    """

    @pytest.fixture
    def _dry_check_fixtures(self, tmp_path):
        """Real saved panels + the auto-tiler's proposal + the real placement.

        `_source_aspect` (the same resolver `build_tiled_sources` uses)
        prefers the tight cropped `content_size_mm` over raw `figsize`, so
        its aspect is not exactly the figsize ratio passed to `_make_panel`
        -- resolve it from the real saved source (no mocks) so `aspects` is
        apples-to-apples with what `build_tiled_sources` will actually use
        internally.
        """
        panels = {
            "A": _make_panel(tmp_path, "A", (3, 2)),
            "B": _make_panel(tmp_path, "B", (2, 2)),
            "C": _make_panel(tmp_path, "C", (2, 3)),
            "D": _make_panel(tmp_path, "D", (5, 2)),
        }
        aspects = {label: _source_aspect(spec) for label, spec in panels.items()}
        width_mm = 180.0
        gap_mm = 1.0
        layout, sizes_mm, canvas_mm = auto_tile_layout(
            aspects, width_mm=width_mm, gap_mm=gap_mm
        )
        sources_mm, real_canvas_mm = build_tiled_sources(
            layout, panels, width_mm=width_mm, gap_mm=gap_mm
        )
        return panels, sizes_mm, canvas_mm, sources_mm, real_canvas_mm

    def test_canvas_size_matches_real_build_tiled_sources(self, _dry_check_fixtures):
        # Arrange
        _panels, _sizes_mm, canvas_mm, _sources_mm, real_canvas_mm = _dry_check_fixtures
        # Act
        # (auto_tile_layout + build_tiled_sources already run in the fixture)
        # Assert: same canvas size (same shared row-height formula).
        assert real_canvas_mm == pytest.approx(canvas_mm)

    def test_per_panel_sizes_match_real_build_tiled_sources(self, _dry_check_fixtures):
        # Arrange
        panels, sizes_mm, _canvas_mm, sources_mm, _real_canvas_mm = _dry_check_fixtures
        # Act
        real_sizes = [sources_mm[panels[label]]["size_mm"] for label in sizes_mm]
        proposed_sizes = [sizes_mm[label] for label in sizes_mm]
        # Assert: same per-panel size_mm (same formula, no drift).
        assert real_sizes == pytest.approx(proposed_sizes)


class TestAutoTileValidation:
    """Empty input fails loud."""

    def test_empty_aspects_raises(self):
        # Arrange
        # Act
        # Assert
        with pytest.raises(ValueError):
            auto_tile_layout({}, width_mm=180)


# EOF
