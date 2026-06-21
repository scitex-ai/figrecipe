#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for constrained_layout panel geometry (figrecipe).

``constrained_layout`` solves the panel rectangles ITERATIVELY to a fixed point
that depends on the construction path, not just the content. The original figure
is built via the mm ``plt.subplots`` helper (which seeds a ``subplots_adjust``
before constrained_layout takes over); a fresh ``reproduce()`` builds a plain
``plt.subplots(constrained_layout=True)``. The two converged to DIFFERENT fixed
points, so the reproduced panels landed ~1 px off the recorded position and the
same-size reproducibility check failed (NeuroVista fig05a, MSE ~907).

The fix freezes the original's settled geometry before its ``savefig`` re-solve
(``_api/_save.py`` -> ``freeze_layout_positions`` for every constrained_layout
figure) so the saved pixels equal the recorded ``bbox_uncropped``, and the
reproducer pins each constrained_layout panel to that recorded rectangle and
takes it out of the layout solver (``_reproducer/_finalize_axes.py`` ->
``pin_constrained_layout_axes``). These tests guard that a constrained_layout
figure reproduces its panel geometry exactly AND reproduces clean in pixels.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr


def _build_constrained_layout_figure():
    """A 2-panel constrained_layout timeline (the NeuroVista fig05a class).

    Built via the mm subplots helper with out-of-axes annotations + vlines +
    left-aligned titles + hidden spines, so its constrained_layout solve is
    sensitive to the construction path (the condition that made the reproduced
    rectangle diverge from the recorded one).
    """
    fig, axes = fr.subplots(
        nrows=2,
        ncols=1,
        axes_width_mm=80,
        axes_height_mm=12.5,
        margin_left_mm=18,
        margin_right_mm=10,
        margin_bottom_mm=14,
        margin_top_mm=10,
        space_h_mm=8,
        panel_labels=False,
        constrained_layout=True,
    )
    days = np.sort(np.random.default_rng(0).uniform(10, 290, size=40))
    for idx, ax in enumerate(axes):
        ax.set_title(
            f"Design {'AB'[idx]} -- timeline schematic", fontsize=9, loc="left"
        )
        ax.vlines(days, 0.0, 1.0, color="#4477aa", linewidth=1.0)
        ax.set_xlim(0, 300)
        ax.set_ylim(-0.1, 1.2)
        ax.set_yticks([])
        ax.text(
            0.02,
            -0.35,
            "pre-day-100 events excluded\n(inclusion floor)",
            transform=ax.ax.transAxes,
            fontsize=6,
            clip_on=False,
        )
        for spine in ("top", "right", "left"):
            ax.ax.spines[spine].set_visible(False)
    axes[1].set_xlabel("post-implant day", fontsize=8)
    return fig


@pytest.fixture(autouse=True)
def cleanup():
    yield
    plt.close("all")


@pytest.fixture
def constrained_layout_saved(tmp_path):
    fig = _build_constrained_layout_figure()
    recipe_path = tmp_path / "cl_timeline.png"
    _, _, result = fr.save(
        fig, str(recipe_path), validate=True, validate_error_level="warning"
    )
    yaml_path = str(recipe_path).replace(".png", ".yaml")
    return {"dir": tmp_path, "yaml": yaml_path, "result": result}


def _recorded_uncropped_bboxes(yaml_path):
    import yaml

    with open(yaml_path) as fh:
        data = yaml.safe_load(fh)
    return {
        key: ax_entry.get("bbox_uncropped")
        for key, ax_entry in data.get("axes", {}).items()
    }


def test_reproduced_panels_match_recorded_position(constrained_layout_saved):
    # Arrange
    recorded = _recorded_uncropped_bboxes(constrained_layout_saved["yaml"])
    rfig, raxes = fr.reproduce(constrained_layout_saved["yaml"])
    rfig.fig.canvas.draw()
    # Act
    reproduced = [
        list(getattr(ax, "ax", ax).get_position().bounds) for ax in np.ravel(raxes)
    ]
    expected = [recorded["r0c0"], recorded["r1c0"]]
    # Assert
    assert np.allclose(reproduced, expected, atol=1e-6)


def test_constrained_layout_figure_reproduces_clean(constrained_layout_saved):
    # Arrange
    artifacts = list(constrained_layout_saved["dir"].glob("*-not-reproduced.*"))
    # Act
    leftover = len(artifacts)
    # Assert
    assert leftover == 0


def test_constrained_layout_figure_validates_under_threshold(constrained_layout_saved):
    # Arrange
    result = constrained_layout_saved["result"]
    # Act
    is_valid = result.valid
    # Assert
    assert is_valid


def test_reproduced_panels_pinned_out_of_layout(constrained_layout_saved):
    # Arrange
    _, raxes = fr.reproduce(constrained_layout_saved["yaml"])
    # Act
    in_layout = [getattr(ax, "ax", ax).get_in_layout() for ax in np.ravel(raxes)]
    # Assert
    assert not any(in_layout)
