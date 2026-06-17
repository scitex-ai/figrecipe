#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Axis scale + explicit limit reproduction (figrecipe, NeuroVista Ask 2).

Two related round-trip guarantees:

(A) ``ax.set_yscale("log")`` / ``set_xscale`` must be recorded and replayed so a
    log (or symlog / logit) axis reproduces as log, not silently as linear. Before
    the fix these setters were not in the recorded decoration allow-list, so the
    decoration list was empty and reproduce() yielded a linear axis.

(B) An explicit ``set_xlim`` / ``set_ylim`` must survive reproduction exactly --
    autoscale re-engaged by later decorations / finalizers must not widen the
    recorded view. The reproducer re-applies the recorded limits last so they win.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import figrecipe as fr


@pytest.fixture()
def log_yaxis_recipe(tmp_path):
    """A recipe whose y-axis was explicitly set to a log scale."""
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot([1, 2, 3, 4], [1, 10, 100, 1000])
    ax.set_yscale("log")
    out = tmp_path / "logy.png"
    fr.save(fig, str(out), validate=False)
    plt.close("all")
    return tmp_path / "logy.yaml"


@pytest.fixture()
def explicit_limits_recipe(tmp_path):
    """A recipe with explicit, non-data x/y limits that autoscale would widen."""
    fig, ax = fr.subplots(axes_width_mm=60, axes_height_mm=40)
    ax.plot(np.arange(11.0), np.arange(11.0))
    ax.set_xlim(2.0, 8.0)
    ax.set_ylim(3.0, 7.0)
    out = tmp_path / "lims.png"
    fr.save(fig, str(out), validate=False)
    plt.close("all")
    return tmp_path / "lims.yaml"


def test_log_yscale_reproduces_as_log(log_yaxis_recipe):
    # Arrange
    _, rax = fr.reproduce(str(log_yaxis_recipe))
    mpl_ax = getattr(rax, "ax", rax)
    # Act
    yscale = mpl_ax.get_yscale()
    plt.close("all")
    # Assert
    assert yscale == "log"


def test_explicit_xlim_reproduces_exactly(explicit_limits_recipe):
    # Arrange
    _, rax = fr.reproduce(str(explicit_limits_recipe))
    mpl_ax = getattr(rax, "ax", rax)
    # Act
    xlim = mpl_ax.get_xlim()
    plt.close("all")
    # Assert
    assert xlim == (2.0, 8.0)


def test_explicit_ylim_reproduces_exactly(explicit_limits_recipe):
    # Arrange
    _, rax = fr.reproduce(str(explicit_limits_recipe))
    mpl_ax = getattr(rax, "ax", rax)
    # Act
    ylim = mpl_ax.get_ylim()
    plt.close("all")
    # Assert
    assert ylim == (3.0, 7.0)
