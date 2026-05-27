#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visualize a dictionary of named RGBA colors as shaded line plots."""

import numpy as np


def vizualize_colors(colors):
    """Visualize a dictionary of named RGBA colors as shaded line plots.

    Parameters
    ----------
    colors : dict
        Mapping of ``name -> rgba`` color.

    Returns
    -------
    tuple
        ``(fig, ax)`` — a figrecipe recording figure and its axes.
    """

    def gen_rand_sample(size=100):
        x = np.linspace(-1, 1, size)
        y = np.random.normal(size=size)
        s = np.random.randn(size)
        return x, y, s

    from .. import subplots

    fig, ax = subplots()

    for _ii, (color_str, rgba) in enumerate(colors.items()):
        xx, yy, ss = gen_rand_sample()
        ax.fill_between(xx, yy - ss, yy + ss, color=rgba, alpha=0.3)
        ax.plot(xx, yy, color=rgba, label=color_str)

    ax.legend()
    return fig, ax


# EOF
