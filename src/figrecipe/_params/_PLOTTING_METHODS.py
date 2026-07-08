#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-23 09:55:10 (ywatanabe)"
# File: /home/ywatanabe/proj/figrecipe/src/figrecipe/PLOTTING_METHODS.py


"""Top-level docstring here"""

PLOTTING_METHODS = {
    "plot",
    "scatter",
    "bar",
    "barh",
    "hist",
    "hist2d",
    "boxplot",
    "violinplot",
    "pie",
    "errorbar",
    "fill",
    "fill_between",
    "fill_betweenx",
    "stackplot",
    "stem",
    "step",
    "imshow",
    "pcolor",
    "pcolormesh",
    "contour",
    "contourf",
    "quiver",
    "barbs",
    "streamplot",
    "hexbin",
    "tripcolor",
    "triplot",
    "tricontour",
    "tricontourf",
    "eventplot",
    "stairs",
    # vlines/hlines draw data-coordinate line collections from arrays (a
    # plotting primitive, unlike the single full-span axvline/axhline
    # reference lines, which are decorations). Recorded so reproduce()
    # replays them -- omitting them dropped every ax.vlines tick on replay
    # (NeuroVista Fig05a schematic: panels rendered empty, large same-size
    # MSE because the whole tick field vanished).
    "vlines",
    "hlines",
    "ecdf",
    "matshow",
    "spy",
    "loglog",
    "semilogx",
    "semilogy",
    "acorr",
    "xcorr",
    "specgram",
    "psd",
    "csd",
    "cohere",
    "angle_spectrum",
    "magnitude_spectrum",
    "phase_spectrum",
    "graph",
    # Coverage-completeness (wrapper-completeness audit): these draw data
    # artists from serializable args and generically record+replay, but were
    # previously unlisted -> forwarded to raw matplotlib -> silently vanished
    # on reproduce(). arrow (dx/dy floats), broken_barh (list of (start,width)
    # tuples + (ymin,height)), table (cellText/cellColours nested lists).
    "arrow",
    "broken_barh",
    "table",
}

# EOF
