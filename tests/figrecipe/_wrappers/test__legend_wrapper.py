"""Tests for figrecipe._wrappers._legend_wrapper.

Covers the deterministic ('stable') filename behaviour of the
``loc='separate'`` legend path: the recorded ``axis_id`` must be derived
from the panel's grid position so the downstream
``<figstem>_<axis_id>_legend.png`` filename is stable across renders.
"""

import pytest


def test_import__wrappers__legend_wrapper_module():
    # Arrange
    module_path = "figrecipe._wrappers._legend_wrapper"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_separate_legend_axis_id_is_stable_across_renders():
    """Re-rendering the same panel yields the same separate-legend axis_id."""
    # Arrange
    import matplotlib.pyplot as plt

    import figrecipe as fr

    fr.load_style("SCITEX")
    ids = []
    # Act
    for _ in range(3):
        fig, ax = fr.subplots()
        ax.plot([0, 1, 2], [0, 1, 0], label="A")
        ax.legend(loc="separate")
        ids.append(fig._separate_legend_params[0]["axis_id"])
        plt.close(fig)
    # Assert
    assert ids[0] == ids[1] == ids[2]


def test_separate_legend_axis_id_is_not_random_hash():
    """The axis_id is a stable position string, not a per-process hash."""
    # Arrange
    import matplotlib.pyplot as plt

    import figrecipe as fr

    fr.load_style("SCITEX")
    fig, ax = fr.subplots()
    ax.plot([0, 1], [0, 1], label="A")
    # Act
    ax.legend(loc="separate")
    axis_id = fig._separate_legend_params[0]["axis_id"]
    plt.close(fig)
    # Assert
    assert axis_id == "0_0"


def test_separate_legends_get_distinct_stable_ids_per_panel():
    """Distinct panels produce distinct (but stable) separate-legend ids."""
    # Arrange
    import matplotlib.pyplot as plt

    import figrecipe as fr

    fr.load_style("SCITEX")
    fig, axes = fr.subplots(1, 2)
    axes[0].plot([0, 1], [0, 1], label="L")
    axes[1].plot([0, 1], [1, 0], label="R")
    # Act
    axes[0].legend(loc="separate")
    axes[1].legend(loc="separate")
    ids = [p["axis_id"] for p in fig._separate_legend_params]
    plt.close(fig)
    # Assert
    assert len(set(ids)) == 2
