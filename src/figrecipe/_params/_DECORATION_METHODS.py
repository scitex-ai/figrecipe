#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-23 09:55:04 (ywatanabe)"
# File: /home/ywatanabe/proj/figrecipe/src/figrecipe/DECORATION_METHODS.py


"""Top-level docstring here"""

DECORATION_METHODS = {
    "set_xlabel",
    "set_ylabel",
    "set_title",
    "set_xlim",
    "set_ylim",
    "set_xscale",  # log/symlog/logit axis scale (replays as a generic decoration)
    "set_yscale",  # log/symlog/logit axis scale (replays as a generic decoration)
    "set_aspect",
    "legend",
    "grid",
    "axhline",
    "axvline",
    # Recorded as decorations (serializable args, generic record+replay): they
    # were previously forwarded to raw matplotlib and silently vanished on
    # reproduce(). They are NOT data-series "plotters" (no CSV builder in
    # figrecipe._dev.list_plotters), so they live here, not in PLOTTING_METHODS.
    "axline",  # arbitrary-slope reference line (xy1/xy2 tuples or slope)
    "arrow",  # single arrow patch (x, y, dx, dy floats)
    "broken_barh",  # bar spans ((start,width)... + (ymin,height))
    "table",  # tabular overlay (cellText/cellColours nested lists)
    "axhspan",
    "axvspan",
    "text",
    "annotate",
    "clabel",
    "axis",  # For axis('off'), axis('on'), axis('equal'), etc.
    "set_xticks",
    "set_yticks",
    "set_xticklabels",
    "set_yticklabels",
    "tick_params",
    "margins",  # For ax.margins(x=0.02) padding
    "rotate_labels",  # figrecipe tick-label rotation (recorded so reproduce replays it)
    # Statistical annotations
    "stat_annotation",  # Comparison brackets with stars/p-values
}

# EOF
