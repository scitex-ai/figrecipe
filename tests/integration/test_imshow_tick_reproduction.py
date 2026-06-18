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
