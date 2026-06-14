"""Tests for figrecipe._api._separate_legend.

Single-source filename policy for ``ax.legend(loc='separate')`` save-time
extraction. Each test follows Arrange / Act / Assert with one assertion.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from figrecipe._api._separate_legend import (  # noqa: E402
    legend_paths_for_figure,
    save_separate_legends,
)


def test_legend_paths_match_figure_stem_plus_suffix():
    # Arrange
    fig_img = Path("/tmp/fig01_traces.png")

    # Act
    legend_img, legend_yml = legend_paths_for_figure(fig_img)

    # Assert
    assert legend_img.name == "fig01_traces_legend.png"


def test_legend_recipe_path_matches_yaml_extension():
    # Arrange
    fig_img = Path("/tmp/fig01_traces.png")

    # Act
    _, legend_yml = legend_paths_for_figure(fig_img)

    # Assert
    assert legend_yml.name == "fig01_traces_legend.yaml"


def test_legend_filename_preserves_pdf_suffix():
    # Arrange
    fig_img = Path("/tmp/fig01_traces.pdf")

    # Act
    legend_img, _ = legend_paths_for_figure(fig_img)

    # Assert
    assert legend_img.suffix == ".pdf"


def test_save_separate_legends_returns_empty_when_no_params(tmp_path):
    # Arrange — plain matplotlib figure without _separate_legend_params.
    fig = plt.figure()
    image_path = tmp_path / "fig.png"

    # Act
    written = save_separate_legends(fig, image_path, save_recipe=False)

    # Assert
    assert written == []
    plt.close(fig)


def test_save_separate_legends_writes_file_with_legend_suffix(tmp_path):
    # Arrange — a single separate-legend request on a matplotlib fig.
    fig, ax = plt.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9], label="x²")
    fig._separate_legend_params = [
        {
            "handles": [line],
            "labels": ["x²"],
            "axis_id": 0,
            "figsize": (3, 1),
            "frameon": True,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
        }
    ]
    image_path = tmp_path / "myfig.png"

    # Act
    written = save_separate_legends(fig, image_path, save_recipe=False)

    # Assert
    assert written[0][0].name == "myfig_legend.png"
    plt.close(fig)


def test_save_separate_legends_writes_recipe_companion(tmp_path):
    # Arrange — same as above but save_recipe=True.
    fig, ax = plt.subplots()
    (line,) = ax.plot([1, 2, 3], [1, 4, 9], label="x²")
    fig._separate_legend_params = [
        {
            "handles": [line],
            "labels": ["x²"],
            "axis_id": 0,
            "figsize": (3, 1),
            "frameon": True,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
        }
    ]
    image_path = tmp_path / "myfig.png"

    # Act
    written = save_separate_legends(fig, image_path, save_recipe=True)

    # Assert
    assert written[0][1] is not None and written[0][1].name == "myfig_legend.yaml"
    plt.close(fig)


def test_multiple_separate_legends_get_numeric_disambiguation(tmp_path):
    # Arrange — two separate legends on the same figure.
    fig, ax = plt.subplots()
    (l1,) = ax.plot([0, 1], [0, 1], label="A")
    (l2,) = ax.plot([0, 1], [1, 0], label="B")
    base = {
        "axis_id": 0,
        "figsize": (3, 1),
        "frameon": True,
        "fancybox": False,
        "shadow": False,
        "kwargs": {},
    }
    fig._separate_legend_params = [
        {"handles": [l1], "labels": ["A"], **base},
        {"handles": [l2], "labels": ["B"], **base},
    ]
    image_path = tmp_path / "myfig.png"

    # Act
    written = save_separate_legends(fig, image_path, save_recipe=False)

    # Assert
    assert [w[0].name for w in written] == [
        "myfig_legend.png",
        "myfig_legend_1.png",
    ]
    plt.close(fig)


# EOF
