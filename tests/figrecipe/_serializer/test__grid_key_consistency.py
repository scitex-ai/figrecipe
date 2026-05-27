#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consistency between YAML axes keys and CSV column prefixes, plus back-compat.

The YAML recipe ``axes:`` keys and the single-CSV column prefixes encode the
same grid (row, col) concept. They must agree (both ``rRcC``), and old recipes
that used the legacy ``ax_R_C`` form must still load.
"""

import glob
import os

import matplotlib
import yaml

matplotlib.use("Agg")

import numpy as np

import figrecipe as fr
from figrecipe._recorder import FigureRecord
from figrecipe._utils._numpy_io import load_single_csv, save_arrays_single_csv


def _build_2x2(tmp_path):
    """Save a 2x2 multi-kind figure and return its yaml path."""
    np.random.seed(0)
    fig, axes = fr.subplots(2, 2)
    axes[0, 0].plot([1, 2, 3], [1, 4, 9], id="line1")
    axes[0, 1].scatter([1, 2, 3], [3, 2, 1], id="sc1")
    axes[1, 0].bar([0, 1, 2], [5, 3, 8], id="bar1")
    axes[1, 1].hist(np.random.randn(200), bins=10, id="h1")
    png = os.path.join(str(tmp_path), "plot.png")
    fr.save(fig, png)
    return glob.glob(os.path.join(str(tmp_path), "*.yaml"))[0]


def test_saved_recipe_axes_keys_use_canonical_grid_form(tmp_path):
    # Arrange
    yaml_path = _build_2x2(tmp_path)
    # Act
    data = yaml.safe_load(open(yaml_path))
    axes_keys = sorted(data["axes"].keys())
    # Assert
    assert axes_keys == ["r0c0", "r0c1", "r1c0", "r1c1"]


def test_single_csv_column_prefixes_match_yaml_axes_keys(tmp_path):
    # Arrange
    arrays = {
        "r0c0": {"line1": {"x": np.array([1, 2, 3]), "y": np.array([1, 4, 9])}},
        "r1c2": {"sc1": {"x": np.array([1, 2]), "y": np.array([3, 2])}},
    }
    out = os.path.join(str(tmp_path), "data.csv")
    save_arrays_single_csv(arrays, out)
    # Act
    import pandas as pd

    cols = list(pd.read_csv(out, nrows=0).columns)
    prefixes = sorted({c.split("_")[0] for c in cols})
    # Assert
    assert prefixes == ["r0c0", "r1c2"]


def test_old_style_recipe_with_legacy_axes_keys_still_loads(tmp_path):
    # Arrange
    yaml_path = _build_2x2(tmp_path)
    data = yaml.safe_load(open(yaml_path))
    legacy_axes = {}
    for key, value in data["axes"].items():
        row, col = key[1:].split("c")
        legacy_axes[f"ax_{row}_{col}"] = value
    data["axes"] = legacy_axes
    # Act
    record = FigureRecord.from_dict(data)
    # Assert
    assert sorted(record.axes.keys()) == ["r0c0", "r0c1", "r1c0", "r1c1"]


def test_legacy_csv_columns_load_into_canonical_keys(tmp_path):
    # Arrange
    legacy = {"ax_0_0": {"trace1": {"x": np.array([1, 2, 3])}}}
    out = os.path.join(str(tmp_path), "legacy.csv")
    save_arrays_single_csv(legacy, out)
    # Act
    result = load_single_csv(out)
    # Assert
    assert "r0c0" in result
