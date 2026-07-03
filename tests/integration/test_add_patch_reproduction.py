#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for ax.add_patch() (figrecipe).

Raw patches were forwarded to matplotlib but never recorded, so they vanished
on replay and the figure failed save-time reproducibility. These tests guard
that supported patches (Rectangle/Circle/Ellipse/Polygon/FancyArrowPatch)
round-trip and that unsupported patch types fail loud at call time.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import pytest
import yaml

import figrecipe as fr


def _patches_of(rax, patch_cls):
    mpl_ax = getattr(rax, "ax", rax)
    return [p for p in mpl_ax.patches if type(p) is patch_cls]


def _find_patch_spec(recipe_path):
    with open(recipe_path) as fh:
        data = yaml.safe_load(fh)
    for ax_entry in data.get("axes", {}).values():
        for call in ax_entry.get("calls", []) + ax_entry.get("decorations", []):
            if call.get("function") == "add_patch":
                return call["kwargs"]["patch_spec"]
    return None


def _save_and_reproduce(fig, recipe_path):
    try:
        fr.save(fig, str(recipe_path))
    except ValueError:
        pass  # geometry/recording asserted regardless of MSE-validation outcome
    yaml_path = str(recipe_path).replace(".png", ".yaml")
    spec = _find_patch_spec(yaml_path)
    _, rax = fr.reproduce(yaml_path)
    return spec, rax


@pytest.fixture
def rectangle_round_trip(tmp_path):
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.Rectangle(
            (0.2, 0.3), 0.4, 0.3, facecolor="red", edgecolor="black", linewidth=2
        )
    )
    spec, rax = _save_and_reproduce(fig, tmp_path / "rect.png")
    return {"spec": spec, "patches": _patches_of(rax, mpatches.Rectangle)}


@pytest.fixture
def circle_round_trip(tmp_path):
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(mpatches.Circle((0.5, 0.5), radius=0.2, facecolor="blue"))
    spec, rax = _save_and_reproduce(fig, tmp_path / "circle.png")
    return {"spec": spec, "patches": _patches_of(rax, mpatches.Circle)}


def test_rectangle_recorded_in_recipe(rectangle_round_trip):
    # Arrange
    spec = rectangle_round_trip["spec"]
    # Act
    recorded_type = spec["type"] if spec else None
    # Assert
    assert recorded_type == "Rectangle"


def test_rectangle_reproduced_once(rectangle_round_trip):
    # Arrange
    patches = rectangle_round_trip["patches"]
    # Act
    count = len(patches)
    # Assert
    assert count == 1


def test_rectangle_geometry_reproduced(rectangle_round_trip):
    # Arrange
    rect = rectangle_round_trip["patches"][0]
    # Act
    geometry = (rect.get_x(), rect.get_y(), rect.get_width(), rect.get_height())
    # Assert
    assert geometry == pytest.approx((0.2, 0.3, 0.4, 0.3))


def test_circle_recorded_in_recipe(circle_round_trip):
    # Arrange
    spec = circle_round_trip["spec"]
    # Act
    recorded_type = spec["type"] if spec else None
    # Assert
    assert recorded_type == "Circle"


def test_circle_reproduced_once(circle_round_trip):
    # Arrange
    patches = circle_round_trip["patches"]
    # Act
    count = len(patches)
    # Assert
    assert count == 1


def test_circle_geometry_reproduced(circle_round_trip):
    # Arrange
    circle = circle_round_trip["patches"][0]
    # Act
    geometry = (circle.center[0], circle.center[1], circle.radius)
    # Assert
    assert geometry == pytest.approx((0.5, 0.5, 0.2))


def test_patch_only_figure_reproduces_clean(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(mpatches.Rectangle((0.1, 0.1), 0.5, 0.5, facecolor="green"))
    # Act
    fr.save(fig, str(tmp_path / "clean.png"))  # raises if the patch is dropped
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))


def test_unsupported_patch_fails_loud(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    wedge = mpatches.Wedge((0.5, 0.5), 0.2, 0, 90)
    # Act
    # adding an unsupported patch type must raise at call time (see Assert)
    # Assert
    with pytest.raises(ValueError, match="cannot record patch type"):
        ax.add_patch(wedge)


@pytest.fixture
def arrow_round_trip(tmp_path):
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        mpatches.FancyArrowPatch(
            (0.2, 0.3),
            (0.7, 0.8),
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.2",
            mutation_scale=12,
            edgecolor="red",
        )
    )
    spec, rax = _save_and_reproduce(fig, tmp_path / "arrow.png")
    return {"spec": spec, "patches": _patches_of(rax, mpatches.FancyArrowPatch)}


def test_arrow_recorded_in_recipe(arrow_round_trip):
    # Arrange
    spec = arrow_round_trip["spec"]
    # Act
    recorded_type = spec["type"] if spec else None
    # Assert
    assert recorded_type == "FancyArrowPatch"


def test_arrow_reproduced_once(arrow_round_trip):
    # Arrange
    patches = arrow_round_trip["patches"]
    # Act
    count = len(patches)
    # Assert
    assert count == 1


def test_arrow_endpoints_reproduced(arrow_round_trip):
    # Arrange
    arrow = arrow_round_trip["patches"][0]
    # Act
    posA, posB = arrow._posA_posB
    endpoints = (*posA, *posB)
    # Assert
    assert endpoints == pytest.approx((0.2, 0.3, 0.7, 0.8))


def test_arrow_connectionstyle_rad_reproduced(arrow_round_trip):
    # Arrange
    spec = arrow_round_trip["spec"]
    # Act
    connectionstyle = spec["connectionstyle"] if spec else ""
    # Assert
    assert "rad=0.2" in connectionstyle


def test_path_based_arrow_fails_loud():
    # Arrange
    from figrecipe._wrappers._axes_patches import extract_patch_spec

    arrow = mpatches.FancyArrowPatch((0.1, 0.1), (0.9, 0.9))
    arrow._posA_posB = None  # a path-based arrow carries no endpoints
    # Act
    # no posA/posB means the arrow cannot round-trip and must fail loud (Assert)
    # Assert
    with pytest.raises(ValueError, match="path-based FancyArrowPatch"):
        extract_patch_spec(arrow)
