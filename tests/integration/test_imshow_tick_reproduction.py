#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for a labelled ax.imshow() (figrecipe).

The live ``ax.imshow`` wrapper hides numeric ticks/spines (the matrix style)
even when the axes carries axis labels. On replay the recorded ``imshow`` ran
as raw matplotlib and ``finalize_special_plots`` skipped suppression for a
labelled image (its ``is_specgram`` heuristic), so the reproduced heatmap grew
back the ticks the original hid and failed save-time reproducibility validation
(NeuroVista Fig 02 panel a). This guards that a labelled ``imshow`` whose ticks
are suppressed at save reproduces clean (no ``*-not-reproduced`` artefact).
"""

import matplotlib

matplotlib.use("Agg")
import numpy as np

import figrecipe as fr


def test_labelled_imshow_reproduces_without_extra_ticks(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.imshow(
        np.linspace(0, 1, 225).reshape(15, 15),
        origin="lower",
        aspect="auto",
        extent=(2.0, 30.0, 60.0, 180.0),
        cmap="hot",
    )
    ax.set_xyt("phase f (Hz)", "amp f (Hz)", "comodulogram")
    # Act
    fr.save(fig, str(tmp_path / "comodulogram.png"))
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))


def test_imshow_with_explicit_ticks_reproduces_keeping_them(tmp_path):
    # The live imshow wrapper hides ticks DURING imshow, so user set_xticks
    # AFTER imshow override it and DO show. On replay those tick calls are
    # decorations replayed before the post-pass, so suppressing unconditionally
    # wiped them (live showed ticks, reproduce hid them) and validation failed.
    # Reproduce must honour explicit ticks on a suppressed-style imshow
    # (NeuroVista Fig 02 panel b -- author labels the Hz bands deliberately).
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.imshow(
        np.linspace(0, 1, 225).reshape(15, 15),
        origin="lower",
        aspect="auto",
        extent=(2.0, 30.0, 60.0, 180.0),
        cmap="hot",
    )
    ax.set_xyt("phase f (Hz)", "amp f (Hz)", "comodulogram")
    ax.set_xticks([8, 16, 24], labels=["8", "16", "24"])
    ax.set_yticks([60, 120, 180], labels=["60", "120", "180"])
    # Act
    fr.save(fig, str(tmp_path / "comodulogram_ticked.png"))
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))


def test_imshow_tile_grid_reproduces_edge_ticks(tmp_path):
    # NeuroVista Fig 02 panel d: a 2-row imshow tile grid where each tile sets
    # ticks explicitly -- sparse Hz ticks on the bottom row / left column,
    # set_xticks([]) elsewhere. #224 cleared the edge tiles' explicit ticks on
    # replay (was green pre-#224 -> MSE 297). Guards that the whole grid
    # round-trips with the edge ticks preserved and the interior suppressed.
    # Arrange
    fig, axes = fr.subplots(
        nrows=2,
        ncols=3,
        axes_width_mm=25,
        axes_height_mm=25,
        margin_left_mm=24,
        margin_bottom_mm=18,
        space_w_mm=4,
        space_h_mm=4,
        panel_labels=False,
    )
    grid = np.add.outer(np.linspace(0, 1, 25), np.linspace(0, 1, 25))
    for r in range(2):
        for c in range(3):
            ax = axes[r, c]
            ax.imshow(
                grid.T,
                origin="lower",
                aspect="auto",
                extent=(2.0, 30.0, 60.0, 180.0),
                cmap="viridis",
                vmin=0.0,
                vmax=2.0,
            )
            if r == 1:
                ax.set_xticks([8, 16, 24], labels=["8", "16", "24"])
            else:
                ax.set_xticks([])
            if c == 0:
                ax.set_yticks([60, 120, 180], labels=["60", "120", "180"])
            else:
                ax.set_yticks([])
            if r == 1 and c == 0:
                ax.set_xlabel("phase f (Hz)")
            if c == 0:
                ax.set_ylabel("amp f (Hz)")
    # Act
    fr.save(fig, str(tmp_path / "tile_grid.png"))
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))
