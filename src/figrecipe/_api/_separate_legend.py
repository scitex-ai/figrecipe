#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save legends flagged with ``loc='separate'`` to a standalone file.

Background
----------
``ax.legend(loc='separate')`` is the figrecipe-extended legend mode that
lifts the legend out of the main panel and writes it as its OWN image so a
busy plot can stay readable. The :mod:`figrecipe._wrappers._legend_wrapper`
side records the request onto ``fig._separate_legend_params``; this module
is the save-time consumer that actually writes the file.

Filename convention
-------------------
For a figure saved as ``<base>.<ext>`` the legend file is::

    <base>_legend.<ext>

so that ``fr.save(fig, "fig01_traces.png")`` produces ``fig01_traces.png``
(the data panel) AND ``fig01_traces_legend.png`` (the lifted legend) — same
stem, ``_legend`` suffix, same extension. The companion recipe is
``fig01_traces_legend.yaml``.

Previously the separate-legend save was delegated to a
``scitex.io._save_modules._legends`` helper, and the resulting filename did
not always follow the figure-base convention (the operator reported it as
"おかしい"). Owning the wiring in figrecipe pins the naming policy to a
single source of truth.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt

__all__ = ["legend_paths_for_figure", "save_separate_legends"]


def legend_paths_for_figure(image_path: Path) -> Tuple[Path, Path]:
    """Return ``(<base>_legend.<ext>, <base>_legend.yaml)`` for *image_path*.

    Parameters
    ----------
    image_path : Path
        The figure image path. The legend's image extension matches.

    Returns
    -------
    (image_legend_path, recipe_legend_path)
    """
    image_path = Path(image_path)
    stem = image_path.stem
    suffix = image_path.suffix or ".png"
    img = image_path.with_name(f"{stem}_legend{suffix}")
    yml = image_path.with_name(f"{stem}_legend.yaml")
    return img, yml


def _legend_recipe(params: Dict[str, Any], image_filename: str) -> Dict[str, Any]:
    """Build a YAML-serializable recipe dict for a single separate legend."""
    return {
        "figrecipe": "1.0",
        "kind": "separate_legend",
        "image": image_filename,
        "axis_id": params.get("axis_id"),
        "figsize": list(params.get("figsize", (4, 2))),
        "frameon": bool(params.get("frameon", True)),
        "fancybox": bool(params.get("fancybox", False)),
        "shadow": bool(params.get("shadow", False)),
        "labels": list(params.get("labels", [])),
        "kwargs": params.get("kwargs", {}),
    }


def save_separate_legends(
    fig,
    image_path: Path,
    *,
    dpi: int = 300,
    save_recipe: bool = True,
) -> List[Tuple[Path, Optional[Path]]]:
    """Write any legends flagged ``loc='separate'`` to their own files.

    Reads ``fig._separate_legend_params`` (populated by
    :func:`figrecipe._wrappers._legend_wrapper._record_separate_legend`) and
    for each entry creates a standalone figure that contains only the
    legend, then writes it next to *image_path* with the ``_legend``
    suffix. Multiple separate legends on one figure are disambiguated with
    a numeric tail: ``<base>_legend.<ext>``, ``<base>_legend_1.<ext>``, …

    Parameters
    ----------
    fig : matplotlib.figure.Figure or RecordingFigure
        The source figure. ``fig._separate_legend_params`` is consulted.
    image_path : Path
        The main figure's image path. Legend filenames are derived from
        ``image_path.stem`` and ``image_path.suffix``.
    dpi : int
        DPI for the legend image.
    save_recipe : bool
        If True, also write ``<base>_legend.yaml`` describing the legend so
        the bundle round-trips.

    Returns
    -------
    list of (image_path, recipe_path or None)
        One entry per legend written. Empty list when the figure has no
        separate-legend requests.
    """
    mpl_fig = getattr(fig, "_fig", fig)
    params_list = getattr(mpl_fig, "_separate_legend_params", None) or []
    if not params_list:
        return []

    image_path = Path(image_path)
    base_img, base_yml = legend_paths_for_figure(image_path)

    written: List[Tuple[Path, Optional[Path]]] = []
    for i, params in enumerate(params_list):
        if i == 0:
            img_path = base_img
            yml_path = base_yml
        else:
            img_path = base_img.with_name(f"{base_img.stem}_{i}{base_img.suffix}")
            yml_path = base_yml.with_name(f"{base_yml.stem}_{i}.yaml")

        # Render the legend on its own figure.
        figsize = tuple(params.get("figsize", (4, 2)))
        legend_fig = plt.figure(figsize=figsize)
        try:
            legend_fig.legend(
                handles=params.get("handles", []),
                labels=params.get("labels", []),
                loc="center",
                frameon=bool(params.get("frameon", True)),
                fancybox=bool(params.get("fancybox", False)),
                shadow=bool(params.get("shadow", False)),
                **(params.get("kwargs") or {}),
            )
            legend_fig.savefig(img_path, dpi=dpi, bbox_inches="tight")
        finally:
            plt.close(legend_fig)

        recipe_path: Optional[Path] = None
        if save_recipe:
            import yaml as _yaml

            recipe_path = yml_path
            recipe = _legend_recipe(params, img_path.name)
            with open(recipe_path, "w") as f:
                _yaml.safe_dump(recipe, f, sort_keys=False)

        written.append((img_path, recipe_path))

    return written


# EOF
