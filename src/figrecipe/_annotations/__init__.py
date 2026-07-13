#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Statistical annotations for matplotlib figures — neutral API.

Provides bracket-and-stars significance markers, plain text annotations,
and automatic y-placement logic.  All functions accept simple Python
dicts/kwargs; there is no dependency on scitex.stats or any scitex package.

Usage
-----
>>> import figrecipe._annotations as ann
>>> import matplotlib.pyplot as plt
>>> fig, ax = plt.subplots()
>>> ax.bar([1, 2, 3], [3, 5, 4])
>>>
>>> # Add a significance bracket
>>> bid = ann.add_stat_bracket(ax, x1=1, x2=2, p_value=0.01, stars="**")
>>>
>>> # List all brackets
>>> ann.list_stat_brackets(ax)
>>> [{'bracket_id': ..., 'x1': 1, 'x2': 2, 'p_value': 0.01, ...}]
>>>
>>> # Remove a bracket by id
>>> ann.remove_stat_bracket(ax, bid)
>>>
>>> # Add a text annotation
>>> tid = ann.add_stat_text(ax, x=2.5, y=4.3, text="n=20")
>>> ann.list_stat_texts(ax)
>>> ann.remove_stat_text(ax, tid)
>>>
>>> # Compute a safe y position for a new bracket
>>> y = ann.auto_y_position(ax, x1=1, x2=3)

Submodules
----------
- _stat_bracket : Bracket rendering and management (add / remove / update / list)
- _stat_text    : Simple text annotation management (add / remove / list)
- _auto_placement : y-position calculation above existing data and brackets
"""

from ._auto_placement import auto_y_position
from ._stat_bracket import (
    add_stat_bracket,
    list_stat_brackets,
    remove_stat_bracket,
    update_stat_bracket,
)
from ._stat_result import StatResult
from ._stat_text import add_stat_text, list_stat_texts, remove_stat_text

__all__ = [
    # Bracket annotations
    "add_stat_bracket",
    "remove_stat_bracket",
    "update_stat_bracket",
    "list_stat_brackets",
    # Text annotations
    "add_stat_text",
    "remove_stat_text",
    "list_stat_texts",
    # Auto-placement
    "auto_y_position",
    # Display port for a computed test result (six-stat doctrine)
    "StatResult",
]

# EOF
