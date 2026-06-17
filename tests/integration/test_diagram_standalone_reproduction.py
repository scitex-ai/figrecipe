#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce round-trip for a standalone figrecipe Diagram.

A standalone diagram enables constrained_layout and was saved with
``bbox_inches="tight"``, which re-measures the ink at SAVE time. The recipe-
reproduced render carries a hair more vertical ink than the original (long box
labels widen ``info.xlim`` at render time), so the tight box differed and
reproducibility validation reported a figure-SIZE mismatch -- writing a
``<stem>-not-reproduced.png`` beside the figure (NeuroVista Fig 02 panel b).

The fix crops standalone diagrams to a RECORDED, dpi-independent ``content_bbox``
so the original save and every reproduce land at identical pixel dimensions.

This guard uses LONG box labels on purpose: short-label diagrams do not trigger
the render-time xlim widening and already round-trip on develop, so they would
not catch the regression.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr


def _long_label_diagram():
    """Build a standalone diagram whose long labels widen xlim at render time."""
    d = fr.Diagram(title="long-label pipeline", width_mm=120, height_mm=40)
    for key in ("alpha", "beta", "gamma", "delta"):
        d.add_box(
            key,
            f"{key.title()} stage\nwith a long label",
            subtitle=f"detail for {key}\nspanning two lines",
            width_mm=22,
            height_mm=18,
            padding_mm=2,
        )
    d.add_arrow("alpha", "beta")
    d.add_arrow("beta", "gamma")
    d.add_arrow("gamma", "delta")
    d.auto_layout(layout="lr", gap_mm=6)
    return d


def test_standalone_long_label_diagram_reproduces_clean(tmp_path):
    # Arrange
    fig, ax = fr.subplots(
        axes_width_mm=120, axes_height_mm=40, margin_top_mm=14, panel_labels=False
    )
    ax.axis("off")
    ax.set_title("long-label pipeline")
    ax.diagram(_long_label_diagram(), id="long_label", track=True, auto_fix=True)
    # Act
    fr.save(fig, str(tmp_path / "diagram.png"))  # raises if it cannot reproduce
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))
