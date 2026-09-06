#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end: correct figures that once FAILED reproducibility validation.

Both cases come from a real document build (scitex-business, 2026-09-02) and
were reproduced on develop on 2026-09-04 before the fixes:

- a single-point date series recorded as the TEXT
  "[np.datetime64('2026-08-08')]" -> replay could not convert it to axis
  units (MSE 284 on a correct figure);
- a custom dash pattern ``ls=(0, (6, 4))`` stored as ``[0, [6, 4]]`` ->
  matplotlib rejected it and the line replayed solid (MSE 240).

Each test saves through figrecipe's public API with validation ON and asserts
the verdict. The control at the end proves the validator can still say no:
a recipe whose data is altered after saving must fail.
"""

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest


@pytest.fixture
def _out(tmp_path):
    return tmp_path


def _save(fig, path):
    import figrecipe as fr

    _img, yml, result = fr.save(
        fig, str(path), validate_error_level="warning", verbose=False
    )
    return yml, result


def test_single_date_point_reproduces(_out):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    dates = np.arange("2026-08-01", "2026-09-28", dtype="datetime64[D]")
    ax.plot(dates, np.linspace(0, 1, dates.size), id="line")
    ax.plot([np.datetime64("2026-08-08")], [0.5], marker="o", ls="none", id="pt")
    # Act
    _yml, result = _save(fig, _out / "single_date_point.png")
    # Assert
    assert result.valid is True


def test_single_date_point_is_recorded_as_data_not_text(_out):
    """The root cause: the one-element list must not become a repr string."""
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([np.datetime64("2026-08-08")], [0.5], marker="o", ls="none", id="pt")
    # Act
    yml, _result = _save(fig, _out / "single_date_point_recipe.png")
    recipe_text = open(yml, encoding="utf-8").read()
    # Assert
    assert "np.datetime64(" not in recipe_text


def test_tuple_linestyle_reproduces(_out):
    # Arrange
    import figrecipe as fr

    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9], ls=(0, (6, 4)), id="dashed")
    # Act
    _yml, result = _save(fig, _out / "tuple_linestyle.png")
    # Assert
    assert result.valid is True


def test_control_altered_recipe_data_fails_validation(_out):
    """Positive control: the validator must still reject a real mismatch."""
    # Arrange
    import figrecipe as fr
    from figrecipe._quality._validator import validate_on_save

    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 4, 9], id="line")
    yml, _ = _save(fig, _out / "control.png")
    y_csv = _out / "control_data" / "line_y.csv"
    y_csv.write_text("9\n1\n5\n", encoding="utf-8")  # not what was drawn
    # Act
    result = validate_on_save(fig, yml)
    # Assert
    assert result.valid is False


# EOF
