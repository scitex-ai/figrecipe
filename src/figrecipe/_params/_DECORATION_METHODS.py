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
    "set_aspect",
    "legend",
    "grid",
    "axhline",
    "axvline",
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
    # Patches: ax.add_patch takes a live Patch artist (not serialisable); the
    # RecordingAxes.add_patch wrapper captures its class+geometry+style instead,
    # so schematic shapes (rectangles, circles, ...) reproduce. Routed here so it
    # replays after the data calls (patch draws on top, as authored).
    "add_patch",
}

# EOF
