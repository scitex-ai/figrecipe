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


def test_imshow_separate_set_xticks_and_set_xticklabels_round_trip(tmp_path):
    # No set_xyt/set_xlabel/set_ylabel here (is_specgram stays False) -- the
    # exact neurovista dogfooding repro: imshow() then a bare ``range(N)``
    # passed to set_xticks() followed by a SEPARATE set_xticklabels() call
    # (not the combined set_xticks(pos, labels=...) form covered above).
    # Two compounding bugs used to drop the labels here: (1) the recorder
    # serialized the raw range() arg to the literal string "range(0, 19)",
    # which failed to replay; (2) finalize_special_plots unconditionally
    # wiped ticks/labels on any imshow axis with no x/y label, clobbering
    # even a correctly-replayed explicit set_xticks/set_xticklabels pair.
    # Arrange
    n = 19
    labels = [f"L{i}" for i in range(n)]
    fig, ax = fr.subplots()
    ax.imshow(np.random.rand(n, n))
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=90)
    fr.save(fig, str(tmp_path / "matrix.yaml"))
    # Act
    _, ax2 = fr.reproduce(str(tmp_path / "matrix.yaml"))
    # Assert
    assert [t.get_text() for t in ax2._ax.get_xticklabels()] == labels
