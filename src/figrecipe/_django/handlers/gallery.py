#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gallery handler — serve template categories and thumbnails."""

import base64
import json
import logging
from pathlib import Path

from django.http import JsonResponse

logger = logging.getLogger(__name__)

_PKG_ROOT = Path(__file__).resolve().parents[2]  # figrecipe/

# Gallery templates are PACKAGE DATA, resolved inside the package.
#
# This used to read:
#     _EXAMPLES_DIR = _PKG_ROOT.parents[1] / "examples" / "02_plot_and_reproduce_all_out"
# which climbs OUT of the package into a repo-relative path. Two things follow,
# and together they made the gallery empty by construction:
#   1. In an installed wheel that resolves into site-packages, where no
#      `examples/` exists — so the gallery was empty in EVERY deployment, not
#      just occasionally.
#   2. That directory is generated example OUTPUT (note the `_out` suffix). It
#      is not committed, so it was absent from a fresh checkout too.
# `handle_gallery_available` includes a template only if its yaml exists, so all
# 18 were filtered out and the UI showed "No templates available for this
# category" — with no error anywhere, because filtering everything out is not a
# failure, it just looks like having nothing.
#
# The assets now ship inside the package (see gallery_templates/), which is what
# makes them survive `pip install`. Keep them here: a path that leaves the
# package cannot be relied on once the package is installed rather than checked out.
_EXAMPLES_DIR = _PKG_ROOT / "_django" / "gallery_templates"

# Category → template mapping (template name → display label)
GALLERY_TEMPLATES = {
    "line": [
        {"name": "plot_plot", "label": "Line", "icon": "fa-chart-line"},
        {"name": "plot_fill_between", "label": "Fill Between", "icon": "fa-chart-area"},
        {"name": "plot_stackplot", "label": "Stack", "icon": "fa-layer-group"},
    ],
    "scatter": [
        {"name": "plot_scatter", "label": "Scatter", "icon": "fa-braille"},
    ],
    "categorical": [
        {"name": "plot_bar", "label": "Bar", "icon": "fa-chart-bar"},
        {"name": "plot_boxplot", "label": "Box", "icon": "fa-box"},
        {"name": "plot_violinplot", "label": "Violin", "icon": "fa-guitar"},
    ],
    "distribution": [
        {"name": "plot_hist", "label": "Histogram", "icon": "fa-chart-column"},
        {"name": "plot_hist2d", "label": "Hist 2D", "icon": "fa-th"},
        {"name": "plot_ecdf", "label": "ECDF", "icon": "fa-chart-line"},
    ],
    "statistical": [
        {"name": "plot_errorbar", "label": "Error Bar", "icon": "fa-arrows-alt-v"},
    ],
    "grid": [
        {"name": "plot_imshow", "label": "Image", "icon": "fa-image"},
        {"name": "plot_matshow", "label": "Matrix", "icon": "fa-th"},
    ],
    "area": [
        {"name": "plot_fill_between", "label": "Fill Between", "icon": "fa-chart-area"},
        {"name": "plot_stackplot", "label": "Stack Plot", "icon": "fa-layer-group"},
    ],
    "contour": [
        {"name": "plot_contourf", "label": "Contour", "icon": "fa-mountain"},
    ],
    "vector": [],
    "special": [
        {"name": "plot_pie", "label": "Pie", "icon": "fa-chart-pie"},
        {"name": "plot_specgram", "label": "Spectrogram", "icon": "fa-wave-square"},
        {"name": "plot_eventplot", "label": "Event", "icon": "fa-timeline"},
        {"name": "plot_graph", "label": "Graph", "icon": "fa-project-diagram"},
    ],
}


def _get_thumbnail_b64(name: str) -> str:
    """Read pre-rendered PNG thumbnail as base64 string."""
    png_path = _EXAMPLES_DIR / f"{name}.png"
    if png_path.exists():
        return base64.b64encode(png_path.read_bytes()).decode("ascii")
    return ""


def handle_gallery_available(request, editor):
    """Return gallery categories with available templates."""
    categories = {}
    for cat_key, templates in GALLERY_TEMPLATES.items():
        items = []
        for tmpl in templates:
            yaml_path = _EXAMPLES_DIR / f"{tmpl['name']}.yaml"
            if yaml_path.exists():
                items.append(
                    {
                        "name": tmpl["name"],
                        "label": tmpl["label"],
                        "icon": tmpl["icon"],
                        "path": str(yaml_path),
                        "has_thumbnail": (
                            _EXAMPLES_DIR / f"{tmpl['name']}.png"
                        ).exists(),
                    }
                )
        if items:
            categories[cat_key] = items

    return JsonResponse({"categories": categories})


def handle_gallery_thumbnail(request, editor, name: str):
    """Return base64 PNG thumbnail for a template."""
    b64 = _get_thumbnail_b64(name)
    if not b64:
        return JsonResponse({"error": f"No thumbnail for {name}"}, status=404)
    return JsonResponse({"image": f"data:image/png;base64,{b64}"})


def handle_gallery_add(request, editor):
    """Copy a gallery template to working dir and load it.

    This delegates to the existing api/switch handler after copying
    the template recipe + data to the working directory.
    """
    import shutil

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    template_name = data.get("template", "")
    if not template_name:
        return JsonResponse({"error": "No template specified"}, status=400)

    yaml_src = _EXAMPLES_DIR / f"{template_name}.yaml"
    if not yaml_src.exists():
        return JsonResponse(
            {"error": f"Template not found: {template_name}"}, status=404
        )

    # Determine working directory
    working_dir = None
    if editor:
        working_dir = getattr(editor, "working_dir", None)
    if not working_dir:
        working_dir = Path.cwd()
    else:
        working_dir = Path(working_dir)

    # Copy YAML recipe
    dest_yaml = working_dir / yaml_src.name
    shutil.copy2(yaml_src, dest_yaml)

    # Copy associated data directory if it exists
    data_dir_name = f"{template_name}_data"
    data_dir_src = _EXAMPLES_DIR / data_dir_name
    data_dir_dest = working_dir / data_dir_name
    if data_dir_src.is_dir() and not data_dir_dest.exists():
        shutil.copytree(data_dir_src, data_dir_dest)

    # Return the recipe path (relative to working dir) for frontend to call api/switch
    return JsonResponse(
        {
            "recipe_path": yaml_src.name,
            "copied": True,
        }
    )
