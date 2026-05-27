#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo plotters registry for all supported figrecipe plotting methods.

Usage
-----
>>> from figrecipe._dev.demo_plotters import REGISTRY, create_all_plots_figure
>>>
>>> # List all available plot types
>>> print(list(REGISTRY.keys()))
>>>
>>> # List by category
>>> from figrecipe._dev.demo_plotters import CATEGORIES
>>> for cat, plots in CATEGORIES.items():
...     print(f"{cat}: {plots}")
>>>
>>> # Create a single figure with all plot types
>>> fig, axes = create_all_plots_figure(fr)
>>>
>>> # Run individual plotter
>>> fig, ax = REGISTRY['plot'](fr, rng, ax)
"""

from ._categories import CATEGORIES, CATEGORY_DISPLAY_NAMES, REPRESENTATIVES
from ._figure_creators import (
    create_all_plots_figure,
    run_all_demos,
    run_individual_demos,
)
from ._gallery_api import generate, get_plot_data, get_plot_spec
from ._helpers import (
    get_plotter,
    get_representative_plots,
    list_plots,
    list_plots_by_category,
)
from ._registry import REGISTRY

# Legacy exports for backwards compatibility
__all__ = [
    "REGISTRY",
    # scitex.plt.gallery-compatible API
    "generate",
    "get_plot_spec",
    "get_plot_data",
    "CATEGORIES",
    "CATEGORY_DISPLAY_NAMES",
    "REPRESENTATIVES",
    "list_plots",
    "list_plots_by_category",
    "get_representative_plots",
    "get_plotter",
    "create_all_plots_figure",
    "run_individual_demos",
    "run_all_demos",
]

# Legacy: export plot_* functions to globals
for _name, _func in REGISTRY.items():
    globals()[f"plot_{_name}"] = _func
    __all__.append(f"plot_{_name}")


def list_demos():
    """Legacy: List all available demo functions."""
    return [f"plot_{name}" for name in REGISTRY.keys()]


# EOF
