#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the deterministic crop-dispatch (_api/_save_crop).

Covers the gate (`wants_content_crop`) across all branches and the
`dispatch_crop` legacy fallback paths (content-aware raster crop + SVG
viewBox crop) that the content_bbox happy-path integration tests don't
exercise. No mocks — dispatch runs against real saved images.
"""

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as _plt  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._api._save_crop import dispatch_crop, wants_content_crop  # noqa: E402


def test_wants_content_crop_false_when_not_croppable():
    # Arrange
    is_croppable = False
    # Act
    result = wants_content_crop(
        is_croppable=is_croppable, use_constrained=True, mm_layout=None
    )
    # Assert
    assert result is False


def test_wants_content_crop_true_for_constrained_raster():
    # Arrange
    is_croppable = True
    # Act
    result = wants_content_crop(
        is_croppable=is_croppable, use_constrained=True, mm_layout=None
    )
    # Assert
    assert result is True


def test_wants_content_crop_true_for_mm_layout_with_margins():
    # Arrange
    mm_layout = {"crop_margin_left_mm": 1}
    # Act
    result = wants_content_crop(
        is_croppable=True, use_constrained=False, mm_layout=mm_layout
    )
    # Assert
    assert result is True


def test_wants_content_crop_false_for_plain_unconstrained_raster():
    # Arrange
    mm_layout = None
    # Act
    result = wants_content_crop(
        is_croppable=True, use_constrained=False, mm_layout=mm_layout
    )
    # Assert
    assert result is False


def test_dispatch_crop_svg_branch_returns_none(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 4], id="l")
    svg_path = Path(os.path.join(str(tmp_path), "fig.svg"))
    fig.fig.savefig(svg_path)
    # Act
    offset = dispatch_crop(
        fig,
        svg_path,
        is_croppable=False,
        is_svg=True,
        use_tight=False,
        use_content_crop=False,
        crop_margin_mm=None,
        crop_margins_mm=(1, 1, 1, 1),
        mm_layout=None,
        dpi=100,
    )
    # Assert
    assert offset is None
    _plt.close(fig.fig)


def test_dispatch_crop_legacy_content_aware_crop_returns_offset(tmp_path):
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 4], id="l")
    png_path = Path(os.path.join(str(tmp_path), "fig.png"))
    fig.fig.savefig(png_path)
    # Act
    offset = dispatch_crop(
        fig,
        png_path,
        is_croppable=True,
        is_svg=False,
        use_tight=False,
        use_content_crop=False,
        crop_margin_mm=2.0,
        crop_margins_mm=(1, 1, 1, 1),
        mm_layout=None,
        dpi=100,
    )
    # Assert
    assert offset is not None
    _plt.close(fig.fig)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])

# EOF
