#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gallery handler — serve template categories, thumbnails, and the first figure.

WHY A CLICK USED TO DO NOTHING
------------------------------
Clicking a template is TWO requests: ``api/gallery/add`` copies the recipe
into the workspace, then ``api/switch`` opens it. They disagreed about where
the workspace IS.

``handle_gallery_add`` resolved ``editor.working_dir or Path.cwd()``. It never
looked at ``?working_dir=`` (what a multi-tenant host injects per user) and
never looked at ``FIGRECIPE_WORKING_DIR`` (what ``figrecipe-editor --dir X``
sets). ``api/switch`` looked at all four. Whenever the server's cwd is not the
workspace — the hosted editor runs from the Django project root, and the CLI
runs from wherever it was launched — the template was written to the SERVER's
directory and the user's workspace stayed empty. Measured on a stock checkout
with ``FIGRECIPE_WORKING_DIR`` pointed at an empty temp dir:

    AFTER add -> workspace contents : []
    AFTER add -> server cwd contents: ['plot_plot.yaml', 'plot_plot_data']

That failed in one of two ways, neither of which named the cause:
  * the server's directory is not writable (a read-only image layer, a
    root-owned cwd) — ``shutil.copy2`` raises, the dispatcher turns it into a
    500, and the UI shows "Failed to add template"; or
  * it IS writable — the copy lands outside the user's workspace, and
    ``api/switch``'s relative-path fallback then found the server's copy and
    reported success, moving the session's whole ``working_dir`` onto the
    server's directory. The figure appeared; the file was never in the
    project, and on a shared host it was in a directory common to every user.

Both are fixed by routing every workspace read/write through ONE resolver,
:func:`~._files_tree.resolve_working_dir`, and by copying via the single
:func:`copy_template_into` used by both the click and the first-figure seed.
"""

import base64
import json
import logging
import shutil
from pathlib import Path

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _files_tree():
    """Import the working-dir resolver lazily.

    ``tests/figrecipe/_django/handlers/test_gallery.py`` loads THIS module by
    file path (``spec_from_file_location``) to exercise asset resolution
    without a configured Django app registry, and a file-path load has no
    parent package for a relative import to bind to — so this is an absolute
    import, deferred to call time. Every caller below runs inside a real
    request, where the app registry is configured.
    """
    from figrecipe._django.handlers import _files_tree as module

    return module

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
TEMPLATES_DIR = _PKG_ROOT / "_django" / "gallery_templates"

# Backwards-compatible alias: the old module-level name is still referenced by
# out-of-tree code and by operators debugging a deployment.
_EXAMPLES_DIR = TEMPLATES_DIR

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


def available_categories():
    """Resolve gallery categories against the on-disk template assets.

    Pure — no Django, no request. Returns ``{category: [item, ...]}`` with
    empty categories dropped, exactly as the API serialises it. Split out of
    :func:`handle_gallery_available` so the asset resolution that broke in
    production is testable without a configured Django app registry.
    """
    if not TEMPLATES_DIR.is_dir():
        # Returning {} here is a 200 with an empty body, which is how this
        # defect stayed silent: nothing in any log said the assets were gone.
        logger.warning(
            "Gallery template assets missing: %s does not exist. The Template "
            "Gallery will render empty. This usually means the package was "
            "built without its gallery_templates package data.",
            TEMPLATES_DIR,
        )
        return {}

    categories = {}
    for cat_key, templates in GALLERY_TEMPLATES.items():
        items = []
        for tmpl in templates:
            yaml_path = TEMPLATES_DIR / f"{tmpl['name']}.yaml"
            if yaml_path.exists():
                items.append(
                    {
                        "name": tmpl["name"],
                        "label": tmpl["label"],
                        "icon": tmpl["icon"],
                        "path": str(yaml_path),
                        "has_thumbnail": (
                            TEMPLATES_DIR / f"{tmpl['name']}.png"
                        ).exists(),
                    }
                )
        if items:
            categories[cat_key] = items

    if not categories:
        logger.warning(
            "Gallery resolved ZERO templates from %s (%d declared). The "
            "Template Gallery will render empty.",
            TEMPLATES_DIR,
            sum(len(v) for v in GALLERY_TEMPLATES.values()),
        )

    return categories


def handle_gallery_available(request, editor):
    """Return gallery categories with available templates."""
    return JsonResponse({"categories": available_categories()})


def handle_gallery_thumbnail(request, editor, name: str):
    """Return base64 PNG thumbnail for a template."""
    b64 = _get_thumbnail_b64(name)
    if not b64:
        return JsonResponse({"error": f"No thumbnail for {name}"}, status=404)
    return JsonResponse({"image": f"data:image/png;base64,{b64}"})


def copy_template_into(template_name: str, working_dir) -> str:
    """Copy ``<template>.yaml`` + ``<template>_data/`` into ``working_dir``.

    Returns the recipe's filename, relative to ``working_dir`` — which is
    exactly what ``api/switch`` expects as its ``path``.

    Raises ``FileNotFoundError`` when the template does not ship. Copying the
    data directory is NOT optional: a recipe names its data by a path
    relative to its own parent, so a recipe copied without its ``_data/``
    sibling loads and then dies in ``_serializer/_load.py`` — the gallery
    looks healthy and the click produces nothing.
    """
    working_dir = Path(working_dir)
    yaml_src = TEMPLATES_DIR / f"{template_name}.yaml"
    if not yaml_src.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    working_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(yaml_src, working_dir / yaml_src.name)

    data_dir_name = f"{template_name}_data"
    data_dir_src = TEMPLATES_DIR / data_dir_name
    if data_dir_src.is_dir():
        shutil.copytree(
            data_dir_src, working_dir / data_dir_name, dirs_exist_ok=True
        )
    return yaml_src.name


def handle_gallery_add(request, editor):
    """Copy a gallery template into the USER's workspace and report its path.

    The frontend then calls ``api/switch`` with the returned ``recipe_path``,
    so this handler and that one must agree on where the workspace is — see
    the module docstring for what happened when they did not.
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    template_name = data.get("template", "")
    if not template_name:
        return JsonResponse({"error": "No template specified"}, status=400)

    working_dir = _files_tree().resolve_working_dir(request, editor)
    try:
        recipe_name = copy_template_into(template_name, working_dir)
    except FileNotFoundError:
        return JsonResponse(
            {"error": f"Template not found: {template_name}"}, status=404
        )
    except OSError as exc:
        # Say WHERE it failed. The old code's PermissionError surfaced as a
        # bare 500 with no directory in it, which is unactionable when the
        # directory is the actual defect.
        logger.exception(
            "[FigRecipe] could not copy template %s into %s",
            template_name,
            working_dir,
        )
        return JsonResponse(
            {"error": f"Could not write template into {working_dir}: {exc}"},
            status=500,
        )

    return JsonResponse(
        {
            "recipe_path": recipe_name,
            "working_dir": str(working_dir),
            "copied": True,
        }
    )


# The figure a brand-new workspace opens on. It is an ordinary shipped recipe
# (two traces, 48 points, ~1.5 KB of csv), copied in by exactly the same code
# path a gallery click takes — so the first impression cannot break while the
# click still works, and vice versa. It is deliberately NOT one of the
# GALLERY_TEMPLATES entries: it carries real axis labels and a title, so what
# the visitor lands on reads as a figure someone made rather than a sample of
# a plot type.
DEMO_TEMPLATE_NAME = "demo_first_figure"


def handle_gallery_demo(request, editor):
    """Return the recipe an empty workspace should open on, seeding it once.

    The editor used to open on an empty grid over an empty file tree — a tool
    that shows neither what it makes nor a way to get there. This gives a
    brand-new visitor a real figure AND the data table behind it on first
    paint.

    Three outcomes, all HTTP 200 so the caller never has to distinguish an
    error from a decision:
      * ``{"recipe_path": "<name>.yaml", "seeded": true}``  — just written.
      * ``{"recipe_path": "<name>.yaml", "seeded": false}`` — already there
        (a returning visitor gets their figure back, and re-seeding is never
        an overwrite of edits they made).
      * ``{"recipe_path": null, "reason": ...}`` — the workspace already has
        recipes of its own. A real project must not be littered with a demo,
        so the caller falls back to the template gallery.
    """
    working_dir = _files_tree().resolve_working_dir(request, editor)
    demo_recipe = working_dir / f"{DEMO_TEMPLATE_NAME}.yaml"

    if demo_recipe.exists():
        return JsonResponse({"recipe_path": demo_recipe.name, "seeded": False})

    if _files_tree().workspace_has_a_recipe(working_dir):
        return JsonResponse(
            {"recipe_path": None, "reason": "workspace already has recipes"}
        )

    try:
        recipe_name = copy_template_into(DEMO_TEMPLATE_NAME, working_dir)
    except (FileNotFoundError, OSError) as exc:
        # A missing first impression is a disappointment, never an outage:
        # the caller falls back to the gallery grid.
        logger.warning(
            "[FigRecipe] could not seed the demo figure into %s: %s",
            working_dir,
            exc,
        )
        return JsonResponse({"recipe_path": None, "reason": str(exc)})

    return JsonResponse({"recipe_path": recipe_name, "seeded": True})
