#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the figrecipe-native gallery API (generate/get_plot_spec/get_plot_data)."""

import pytest


def test_gallery_exposes_generate():
    # Arrange
    import figrecipe as fr

    # Act
    present = hasattr(fr.gallery, "generate")

    # Assert
    assert present


def test_gallery_exposes_get_plot_spec():
    # Arrange
    import figrecipe as fr

    # Act
    present = hasattr(fr.gallery, "get_plot_spec")

    # Assert
    assert present


def test_gallery_exposes_get_plot_data():
    # Arrange
    import figrecipe as fr

    # Act
    present = hasattr(fr.gallery, "get_plot_data")

    # Assert
    assert present


def test_get_plot_spec_returns_plot_type():
    # Arrange
    import figrecipe as fr

    # Act
    spec = fr.gallery.get_plot_spec("line_curve", "plot")

    # Assert
    assert spec["plot_type"] == "plot"


def test_get_plot_spec_returns_category():
    # Arrange
    import figrecipe as fr

    # Act
    spec = fr.gallery.get_plot_spec("line_curve", "plot")

    # Assert
    assert spec["category"] == "line_curve"


def test_get_plot_spec_rejects_unknown_category():
    # Arrange
    import figrecipe as fr

    # Act
    call = lambda: fr.gallery.get_plot_spec("no_such_category", "plot")

    # Assert
    with pytest.raises(ValueError):
        call()


def test_get_plot_spec_rejects_unknown_plot():
    # Arrange
    import figrecipe as fr

    # Act
    call = lambda: fr.gallery.get_plot_spec("line_curve", "no_such_plot")

    # Assert
    with pytest.raises(ValueError):
        call()


def test_get_plot_data_returns_dataframe_for_line_plot():
    # Arrange
    import pandas as pd

    import figrecipe as fr

    # Act
    df = fr.gallery.get_plot_data("line_curve", "plot")

    # Assert
    assert isinstance(df, pd.DataFrame)


def test_get_plot_data_returns_nonempty_for_line_plot():
    # Arrange
    import figrecipe as fr

    # Act
    df = fr.gallery.get_plot_data("line_curve", "plot")

    # Assert
    assert not df.empty


def test_generate_for_single_category_produces_png(tmp_path):
    # Arrange
    import figrecipe as fr

    # Act
    results = fr.gallery.generate(
        tmp_path / "gallery", category="line_curve", verbose=False
    )

    # Assert
    assert len(results["png"]) > 0


def test_generate_for_single_category_has_no_errors(tmp_path):
    # Arrange
    import figrecipe as fr

    # Act
    results = fr.gallery.generate(
        tmp_path / "gallery", category="line_curve", verbose=False
    )

    # Assert
    assert results["errors"] == []


def test_generate_for_single_plot_type_writes_png_file(tmp_path):
    # Arrange
    import figrecipe as fr

    out = tmp_path / "gallery"

    # Act
    fr.gallery.generate(out, plot_type="scatter", verbose=False)

    # Assert
    assert list(out.rglob("scatter.png"))


# EOF
