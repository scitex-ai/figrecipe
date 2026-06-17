#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save -> reproduce line-width fidelity (figrecipe regression).

Guards the fix that removed the reproducer's ``apply_line_styles()`` pass.
That pass force-set every replayed data line to the thin *trace* width
(``linewidth_mm`` 0.8mm -> ``trace_mm`` 0.12mm), clobbered explicit ``lw=``,
and broke reproducibility — a bare default-styled plot failed save-time
validation (MSE ~363). Ordinary lines now inherit ``rcParams["lines.linewidth"]``
(= ``linewidth_mm``) applied by ``apply_style_mm``; explicit and ``lw="signal"``
widths are recorded numerically and replay verbatim. See
``figrecipe/_reproducer/_core.py``.
"""

import matplotlib

matplotlib.use("Agg")
import pytest
from matplotlib.lines import Line2D

import figrecipe as fr


def _reproduced_data_line_width(yaml_path):
    """Reproduce a recipe and return the width of its first data line (pt)."""
    _, rax = fr.reproduce(str(yaml_path))
    mpl_ax = getattr(rax, "ax", rax)
    widths = [
        child.get_linewidth()
        for child in mpl_ax.get_children()
        if isinstance(child, Line2D) and len(child.get_xdata()) > 2
    ]
    assert widths, "no data line found in reproduced axes"
    return widths[0]


def test_ordinary_line_width_survives_round_trip(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    (line,) = ax.plot([0, 1, 2], [0, 1, 0])
    live_lw = line.get_linewidth()
    # Act
    try:
        fr.save(fig, str(tmp_path / "ordinary.png"))
    except ValueError:
        pass  # width asserted below regardless of MSE-validation outcome
    reproduced_lw = _reproduced_data_line_width(tmp_path / "ordinary.yaml")
    # Assert
    assert reproduced_lw == pytest.approx(live_lw, rel=1e-6)


def test_explicit_linewidth_survives_round_trip(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2], [0, 1, 0], linewidth=2.5)
    # Act
    try:
        fr.save(fig, str(tmp_path / "explicit.png"))
    except ValueError:
        pass
    reproduced_lw = _reproduced_data_line_width(tmp_path / "explicit.yaml")
    # Assert
    assert reproduced_lw == pytest.approx(2.5, rel=1e-6)


def test_default_styled_plot_reproduces_without_artifact(tmp_path):
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2], [0, 1, 0])
    # Act
    fr.save(fig, str(tmp_path / "clean.png"))  # raises on the MSE ~363 regression
    # Assert
    assert not list(tmp_path.glob("*-not-reproduced.*"))
