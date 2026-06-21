#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for hidden axes spines (figrecipe).

A script that hides ALL four spines (e.g. the NeuroVista Fig03b 4x4 Cliff's
delta grid: colored Rectangle cells + cell text + a thick-edged "pool" outline,
all spines off) used to fail save-time reproducibility with MSE ~117: the recipe
never recorded spine visibility, so the style pass on replay only hid top+right
and a spurious left+bottom L-shaped spine survived.

The fix captures the FINAL rendered spine visibility per axes at save time
(``AxesRecord.final_spines``) and the reproducer re-applies it last. These tests
guard that the visibility round-trips and that the grid reproduces clean.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pytest
import yaml

import figrecipe as fr


def _grid_with_hidden_spines(ax):
    """A 2x2 colored-Rectangle grid + cell text + a thick "pool" outline, with
    every spine hidden -- a minimal stand-in for the Fig03b construct."""
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(-0.6, 1.6)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    fills = ["#a69695", "#bb847e", "#8f9aa1", "#7f95a3"]
    for idx, (row, col) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
        ax.add_patch(
            mpatches.Rectangle(
                (col - 0.5, (1 - row) - 0.5),
                1.0,
                1.0,
                facecolor=fills[idx],
                edgecolor="#9e9e9e",
                linewidth=0.6,
            )
        )
        ax.text(col, 1 - row, f"{idx + 1}\n+0.10", ha="center", va="center", fontsize=6)
    # Thick-edged "pool" outline on one cell (facecolor none).
    ax.add_patch(
        mpatches.Rectangle(
            (-0.5, 0.5), 1.0, 1.0, facecolor="none", edgecolor="#ff4632", linewidth=2.0
        )
    )
    for spine in ("top", "right", "left", "bottom"):
        ax.ax.spines[spine].set_visible(False)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    plt.close("all")


@pytest.fixture
def hidden_spine_grid(tmp_path):
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=40)
    _grid_with_hidden_spines(ax)
    recipe_path = tmp_path / "grid.png"
    fr.save(fig, str(recipe_path), validate=True, validate_error_level="warning")
    yaml_path = str(recipe_path).replace(".png", ".yaml")
    return {"dir": tmp_path, "yaml": yaml_path}


def _final_spines(yaml_path):
    with open(yaml_path) as fh:
        data = yaml.safe_load(fh)
    for ax_entry in data.get("axes", {}).values():
        if "final_spines" in ax_entry:
            return ax_entry["final_spines"]
    return None


def test_final_spines_recorded(hidden_spine_grid):
    # Arrange
    spines = _final_spines(hidden_spine_grid["yaml"])
    # Act
    all_hidden = spines is not None and not any(spines.values())
    # Assert
    assert all_hidden


def test_left_spine_hidden_on_replay(hidden_spine_grid):
    # Arrange
    _, rax = fr.reproduce(hidden_spine_grid["yaml"])
    # Act
    left_visible = getattr(rax, "ax", rax).spines["left"].get_visible()
    # Assert
    assert left_visible is False


def test_bottom_spine_hidden_on_replay(hidden_spine_grid):
    # Arrange
    _, rax = fr.reproduce(hidden_spine_grid["yaml"])
    # Act
    bottom_visible = getattr(rax, "ax", rax).spines["bottom"].get_visible()
    # Assert
    assert bottom_visible is False


def test_hidden_spine_grid_reproduces_clean(hidden_spine_grid):
    # Arrange
    artifacts = list(hidden_spine_grid["dir"].glob("*-not-reproduced.*"))
    # Act
    leftover = len(artifacts)
    # Assert
    assert leftover == 0


def test_hidden_spine_grid_validates_under_threshold(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=40)
    _grid_with_hidden_spines(ax)
    # Act
    _, _, result = fr.save(
        fig, str(tmp_path / "grid2.png"), validate=True, validate_error_level="warning"
    )
    # Assert
    assert result.valid
