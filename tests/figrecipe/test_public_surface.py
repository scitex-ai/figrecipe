#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the extended figrecipe public surface.

These names were ported from the scitex.plt umbrella so that
``from figrecipe.pyplot import *`` + ``from figrecipe import *`` cover the
umbrella's full public API and ``scitex.plt`` can become a pure alias.
"""

import pandas as pd
import pytest

# The 21 names the umbrella requires from the figrecipe namespaces.
UMBRELLA_NAMES = [
    "ALL_KINDS",
    "DATA_KINDS",
    "KIND_ALIASES",
    "LABEL_KINDS",
    "MATRIX_KINDS",
    "XY_KINDS",
    "STYLE",
    "apply_style",
    "styles",
    "presets",
    "color",
    "build_spec",
    "build_spec_from_csv",
    "render_spec_to_bytes",
    "draw_graph",
    "smart_align",
    "enable_svg",
    "edit",
    "gallery",
    "termplot",
    "utils",
]


@pytest.mark.parametrize("name", UMBRELLA_NAMES)
def test_top_level_namespace_exposes_umbrella_name(name):
    # Arrange
    import figrecipe as fr

    # Act
    has_attr = hasattr(fr, name)

    # Assert
    assert has_attr, f"figrecipe.{name} missing"


@pytest.mark.parametrize("name", UMBRELLA_NAMES)
def test_pyplot_namespace_exposes_umbrella_name(name):
    # Arrange
    import figrecipe.pyplot as fpp

    # Act
    has_attr = hasattr(fpp, name)

    # Assert
    assert has_attr, f"figrecipe.pyplot.{name} missing"


def test_import_star_union_covers_all_umbrella_names():
    # Arrange
    ns = {}

    # Act
    exec("from figrecipe.pyplot import *", ns)
    exec("from figrecipe import *", ns)
    missing = [n for n in UMBRELLA_NAMES if n not in ns]

    # Assert
    assert missing == []


def test_xy_kinds_registry_contains_line():
    # Arrange
    import figrecipe as fr

    # Act
    kinds = fr.XY_KINDS

    # Assert
    assert "line" in kinds


def test_kind_aliases_maps_box_to_boxplot():
    # Arrange
    import figrecipe as fr

    # Act
    resolved = fr.KIND_ALIASES["box"]

    # Assert
    assert resolved == "boxplot"


def test_build_spec_line_produces_line_plot_entry():
    # Arrange
    import figrecipe as fr

    # Act
    spec = fr.build_spec({"kind": "line", "y": "1,2,3,4", "title": "Demo"})

    # Assert
    assert spec["plots"][0]["type"] == "line"


def test_build_spec_from_csv_records_data_file():
    # Arrange
    import figrecipe as fr

    csv = "/tmp/_fr_spec_builder_test.csv"
    with open(csv, "w") as f:
        f.write("x,y\n0,1\n1,2\n")

    # Act
    spec = fr.build_spec_from_csv(csv, {"kind": "line", "x_col": "x", "y_col": "y"})

    # Assert
    assert spec["plots"][0]["data_file"] == csv


def test_render_spec_to_bytes_returns_png_bytes():
    # Arrange
    import figrecipe as fr

    spec = fr.build_spec({"kind": "line", "y": "1,2,3"})

    # Act
    png = fr.render_spec_to_bytes(spec, dpi=72)

    # Assert
    assert png[:4] == b"\x89PNG"


def test_add_hue_col_appends_hue_column():
    # Arrange
    import figrecipe as fr

    df = pd.DataFrame({"a": [1.0, 2.0]})

    # Act
    out = fr.colors.add_hue_col(df)

    # Assert
    assert "hue" in out.columns


def test_smart_align_aliases_align_smart():
    # Arrange
    import figrecipe as fr

    # Act
    same = fr.smart_align is fr.align_smart

    # Assert
    assert same


def test_edit_aliases_gui():
    # Arrange
    import figrecipe as fr

    # Act
    same = fr.edit is fr.gui

    # Assert
    assert same
