#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registry for demo plotter functions."""

import importlib
from pathlib import Path
from typing import Callable, Dict

import scitex_logging as slogging

console = slogging.getConsole(f"{__name__}.console")

# Registry: plot_name -> plotter function
REGISTRY: Dict[str, Callable] = {}

# Get demo directory
_demo_dir = Path(__file__).parent

# Category subdirectories
_category_dirs = [
    "line_curve",
    "scatter_points",
    "bar_categorical",
    "distribution",
    "image_matrix",
    "contour_surface",
    "spectral_signal",
    "vector_flow",
    "special",
]

# Collect all plot_*.py files from subdirectories
_demo_files = []
for _cat_dir in _category_dirs:
    _cat_path = _demo_dir / _cat_dir
    if _cat_path.is_dir():
        _demo_files.extend(sorted(_cat_path.glob("plot_*.py")))

# Import all demo functions into registry
for _file in _demo_files:
    _module_name = _file.stem  # e.g., plot_scatter
    _plot_name = _module_name.replace("plot_", "")  # e.g., scatter
    _func_name = _module_name  # e.g., plot_scatter
    _cat_dir = _file.parent.name  # e.g., scatter_points
    try:
        _module = importlib.import_module(
            f".{_cat_dir}.{_module_name}", package=__name__.rsplit(".", 1)[0]
        )
        if hasattr(_module, _func_name):
            REGISTRY[_plot_name] = getattr(_module, _func_name)
    except ImportError as e:
        console.warning(f"Warning: Could not import {_cat_dir}.{_module_name}: {e}")

# EOF
