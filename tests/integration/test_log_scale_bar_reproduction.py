#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for a bar chart on a log y-axis with text + legend.

This figure (bar x2 + ``set_yscale("log")`` + ``set_ylim`` + legend + several
``text()`` annotations under constrained_layout) was saved with
``bbox_inches="tight"``, which re-measures the ink to crop. constrained_layout
solves the axes rectangle ITERATIVELY -- one draw leaves it part-way -- so the
tight-crop SIZE depended on how many times the figure had been drawn before the
save. The original ``fig`` is drawn many times over its build/save while a fresh
``reproduce()``-d figure is drawn only a few, so the two landed on different
layout iterates: their tight crops differed by a few pixels and reproducibility
validation reported a figure-SIZE mismatch, writing a ``<stem>-not-reproduced.png``
beside the figure (NeuroVista Fig 02 panel c, "throughput bench").

The fix settles constrained_layout to its converged fixed point before the tight
save, so the saved size is a pure function of the content and the original +
every reproduce land at identical pixel dimensions.

The log y-axis is load-bearing for this guard: it forces the iterative-layout +
tight-crop interaction that exposed the non-determinism.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np

import figrecipe as fr


def _build_log_bar_figure():
    """Build a bar + log-y figure with legend and out-of-axes text annotations."""
    fig, ax = fr.subplots(axes_width_mm=58, axes_height_mm=42, panel_labels=False)
    ax.set_title("Throughput", pad=20)
    floor = 0.0667
    x = np.array([0, 1, 2])
    width = 0.38
    ax.bar(
        x - width / 2,
        [0.62, 11.0, 140.0],
        width=width,
        bottom=floor,
        label="CPU",
    )
    ax.bar(
        x + width / 2,
        [0.2, 0.9, 1.46],
        width=width,
        bottom=floor,
        label="GPU",
    )
    ax.set_yscale("log")
    ax.set_ylim(floor, 420.0)
    ax.set_xticks(x)
    ax.set_xticklabels(["small\nbatch=1", "medium\nbatch=10", "large\nbatch=127"])
    ax.set_ylabel("Wall-clock per window (s)")
    for xi, yv, s in zip(x, [0.93, 16.5, 210.0], ["3x", "12x", "96x"]):
        ax.text(xi, yv, s, ha="center", va="bottom", weight="bold", fontsize=6)
    ax.legend(loc="upper left", frameon=False)
    ax.text(0.0, -0.34, "illustrative footnote", transform=ax.ax.transAxes, va="top")
    return fig


def test_log_scale_bar_reproduces_clean(tmp_path):
    # Arrange
    fig = _build_log_bar_figure()
    # Act
    fr.save(fig, str(tmp_path / "throughput.png"))  # raises if it cannot reproduce
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))
