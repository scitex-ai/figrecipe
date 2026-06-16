#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for crop-aware mm-composition placement + recipe roundtrip.

Covers panel_rel_bbox's three branches and the save->load roundtrip of the
crop-aware fields. Regression guard: bbox_uncropped was serialized by
AxesRecord.to_dict but NOT read back by from_dict, which silently disabled
crop-aware composition for every file-loaded recipe (the normal fr.compose
path) -- it degraded to the legacy bbox and looked half-wired.
"""

from figrecipe._composition._crop_aware import panel_rel_bbox
from figrecipe._recorder._core import AxesRecord, FigureRecord


def _axes(**kw):
    ax = AxesRecord(position=(0, 0))
    for k, v in kw.items():
        setattr(ax, k, v)
    return ax


def test_panel_rel_bbox_maps_axes_relative_to_content_box():
    # Arrange
    fig = FigureRecord(content_bbox=[0.0, 0.0, 0.5, 0.5])
    ax = _axes(bbox_uncropped=[0.25, 0.25, 0.25, 0.25], bbox=[9, 9, 9, 9])
    # Act
    rel = panel_rel_bbox(fig, ax)
    # Assert
    assert rel == (0.5, 0.5, 0.5, 0.5)


def test_panel_rel_bbox_falls_back_to_legacy_bbox():
    # Arrange
    fig = FigureRecord()
    ax = _axes(bbox=[0.1, 0.2, 0.7, 0.6])
    # Act
    rel = panel_rel_bbox(fig, ax)
    # Assert
    assert rel == (0.1, 0.2, 0.7, 0.6)


def test_panel_rel_bbox_fills_panel_when_no_bbox():
    # Arrange
    fig = FigureRecord()
    ax = _axes()
    # Act
    rel = panel_rel_bbox(fig, ax)
    # Assert
    assert rel == (0.0, 0.0, 1.0, 1.0)


def test_panel_rel_bbox_guards_zero_size_content_box():
    # Arrange
    fig = FigureRecord(content_bbox=[0.0, 0.0, 0.0, 0.0])
    ax = _axes(bbox_uncropped=[0.1, 0.1, 0.2, 0.2], bbox=[0.3, 0.3, 0.3, 0.3])
    # Act
    rel = panel_rel_bbox(fig, ax)
    # Assert
    assert rel == (0.3, 0.3, 0.3, 0.3)


def test_content_bbox_survives_recipe_roundtrip():
    # Arrange
    fig = FigureRecord(content_bbox=[0.01, 0.02, 0.97, 0.95])
    # Act
    restored = FigureRecord.from_dict(fig.to_dict())
    # Assert
    assert restored.content_bbox == [0.01, 0.02, 0.97, 0.95]


def test_content_size_mm_survives_recipe_roundtrip():
    # Arrange
    fig = FigureRecord(content_size_mm=[120.0, 90.0])
    # Act
    restored = FigureRecord.from_dict(fig.to_dict())
    # Assert
    assert restored.content_size_mm == [120.0, 90.0]


def test_bbox_uncropped_survives_recipe_roundtrip():
    # Arrange
    fig = FigureRecord()
    fig.axes["r0c0"] = AxesRecord(position=(0, 0), bbox_uncropped=[0.1, 0.2, 0.3, 0.4])
    # Act
    restored = FigureRecord.from_dict(fig.to_dict())
    # Assert
    assert restored.axes["r0c0"].bbox_uncropped == [0.1, 0.2, 0.3, 0.4]


def test_crop_aware_branch_fires_on_roundtripped_record():
    # Arrange
    fig = FigureRecord(content_bbox=[0.0, 0.0, 0.5, 0.5])
    fig.axes["r0c0"] = AxesRecord(
        position=(0, 0), bbox=[9, 9, 9, 9], bbox_uncropped=[0.25, 0.25, 0.25, 0.25]
    )
    restored = FigureRecord.from_dict(fig.to_dict())
    # Act
    rel = panel_rel_bbox(restored, restored.axes["r0c0"])
    # Assert
    assert rel == (0.5, 0.5, 0.5, 0.5)


# EOF
