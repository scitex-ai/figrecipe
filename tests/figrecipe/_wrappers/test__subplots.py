"""Smoke import mirror for figrecipe._wrappers._subplots.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import numpy as np
import pytest

import figrecipe as fr


def test_import__wrappers__subplots_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._wrappers._subplots"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _sharing_matrix(axes, dimension):
    panels = [ax._ax for ax in np.asarray(axes, dtype=object).flat]
    grouper = getattr(panels[0], f"get_shared_{dimension}_axes")()
    return [[grouper.joined(left, right) for right in panels] for left in panels]


@pytest.mark.parametrize("dimension", ["x", "y"])
@pytest.mark.parametrize("mode", [True, "row", "col", "all", False, "none"])
def test_shared_axes_survive_recipe_roundtrip(tmp_path, dimension, mode):
    # Arrange: a real grid and recipe, with both partial-sharing directions.
    fig, axes = fr.subplots(2, 2, figsize=(4, 4), **{f"share{dimension}": mode})
    for ax in axes.flat:
        ax.plot([0, 1, 2], [1, 3, 2])
    expected = _sharing_matrix(axes, dimension)
    path = tmp_path / "shared.yaml"
    fig.save_recipe(path)
    # Act
    _, replayed = fr.reproduce(path)
    # Assert
    assert _sharing_matrix(replayed, dimension) == expected


def test_shared_x_tick_labels_stay_suppressed_with_outside_legends(tmp_path):
    # Arrange: the reported multi-panel shape with actual outside legends.
    fig, axes = fr.subplots(2, 1, sharex=True, figsize=(4, 4))
    for ax in axes:
        ax.plot([0, 1, 2], [1, 3, 2], label="Outside legend")
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.fig.canvas.draw()
    expected = [len(ax._ax.get_xticklabels()) for ax in axes]
    path = tmp_path / "outside.yaml"
    fig.save_recipe(path)
    # Act
    replayed_fig, replayed = fr.reproduce(path)
    replayed_fig.fig.canvas.draw()
    # Assert
    assert [len(ax._ax.get_xticklabels()) for ax in replayed] == expected


def test_legacy_recipe_still_has_unshared_axes():
    # Arrange
    from figrecipe._recorder import FigureRecord

    legacy = {"figure": {"figsize": [4, 4], "dpi": 100}, "axes": {}}
    # Act
    record = FigureRecord.from_dict(legacy)
    # Assert
    assert (record.sharex, record.sharey) == (False, False)
