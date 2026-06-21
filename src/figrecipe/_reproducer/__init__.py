#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure reproduction module.

This module provides functionality to reproduce figures from recipe files.
The public API exposes three main functions:
- reproduce: Reproduce a figure from a recipe file
- reproduce_from_record: Reproduce a figure from a FigureRecord object
- get_recipe_info: Get information about a recipe without reproducing it
"""

from ._core import reproduce, reproduce_from_record
from ._recipe_info import get_recipe_info

__all__ = [
    "reproduce",
    "reproduce_from_record",
    "get_recipe_info",
]
