#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Statistical annotation handlers — add/remove/update/list brackets."""

import json
from pathlib import Path

import scitex_logging as slogging

from ..._utils._optional import missing_extra

try:
    from django.http import JsonResponse
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

logger = slogging.getLogger(__name__)


def handle_stats_add_bracket(request, editor):
    """Add a statistical significance bracket to the figure."""
    from figrecipe._annotations import add_stat_bracket
    from figrecipe._editor._helpers import render_with_overrides

    data = json.loads(request.body) if request.body else {}
    ax_index = data.get("ax_index", 0)
    x1 = data.get("x1")
    x2 = data.get("x2")
    p_value = data.get("p_value", 0.0)

    if x1 is None or x2 is None:
        return JsonResponse({"error": "Missing x1 or x2"}, status=400)

    try:
        fig = editor.fig
        axes_list = fig.get_axes()
        if ax_index >= len(axes_list):
            return JsonResponse(
                {"error": f"Invalid axis index: {ax_index}"}, status=400
            )

        ax = axes_list[ax_index]
        bracket_id = add_stat_bracket(
            ax,
            x1=x1,
            x2=x2,
            p_value=p_value,
            stars=data.get("stars", ""),
            y=data.get("y"),
            style=data.get("style", "bracket"),
            label=data.get("label", ""),
            effect_size=data.get("effect_size"),
            effect_size_name=data.get("effect_size_name"),
            bracket_id=data.get("bracket_id"),
        )

        img, bboxes, size = render_with_overrides(
            editor.fig, editor.get_effective_style(), editor.dark_mode
        )
        return JsonResponse(
            {
                "success": True,
                "bracket_id": bracket_id,
                "image": img,
                "bboxes": bboxes,
                "img_size": {"width": size[0], "height": size[1]},
            }
        )

    except Exception as e:
        logger.exception("[FigRecipe] stats/add_bracket failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_stats_remove_bracket(request, editor):
    """Remove a bracket by ID."""
    from figrecipe._annotations import remove_stat_bracket

    data = json.loads(request.body) if request.body else {}
    bracket_id = data.get("bracket_id")
    ax_index = data.get("ax_index", 0)

    if not bracket_id:
        return JsonResponse({"error": "Missing bracket_id"}, status=400)

    try:
        fig = editor.fig
        axes_list = fig.get_axes()
        if ax_index >= len(axes_list):
            return JsonResponse(
                {"error": f"Invalid axis index: {ax_index}"}, status=400
            )

        ax = axes_list[ax_index]
        removed = remove_stat_bracket(ax, bracket_id)

        if not removed:
            return JsonResponse(
                {"error": f"Bracket not found: {bracket_id}"}, status=404
            )

        from figrecipe._editor._helpers import render_with_overrides

        img, bboxes, size = render_with_overrides(
            editor.fig, editor.get_effective_style(), editor.dark_mode
        )
        return JsonResponse(
            {
                "success": True,
                "image": img,
                "bboxes": bboxes,
                "img_size": {"width": size[0], "height": size[1]},
            }
        )

    except Exception as e:
        logger.exception("[FigRecipe] stats/remove_bracket failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_stats_update_bracket(request, editor):
    """Update bracket properties (position, style, label)."""
    from figrecipe._annotations import update_stat_bracket

    data = json.loads(request.body) if request.body else {}
    bracket_id = data.get("bracket_id")
    ax_index = data.get("ax_index", 0)

    if not bracket_id:
        return JsonResponse({"error": "Missing bracket_id"}, status=400)

    try:
        fig = editor.fig
        axes_list = fig.get_axes()
        if ax_index >= len(axes_list):
            return JsonResponse(
                {"error": f"Invalid axis index: {ax_index}"}, status=400
            )

        ax = axes_list[ax_index]
        update_kwargs = {
            k: v for k, v in data.items() if k not in ("bracket_id", "ax_index")
        }
        updated = update_stat_bracket(ax, bracket_id, **update_kwargs)

        if not updated:
            return JsonResponse(
                {"error": f"Bracket not found: {bracket_id}"}, status=404
            )

        from figrecipe._editor._helpers import render_with_overrides

        img, bboxes, size = render_with_overrides(
            editor.fig, editor.get_effective_style(), editor.dark_mode
        )
        return JsonResponse(
            {
                "success": True,
                "image": img,
                "bboxes": bboxes,
                "img_size": {"width": size[0], "height": size[1]},
            }
        )

    except Exception as e:
        logger.exception("[FigRecipe] stats/update_bracket failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_stats_import_plot_spec(request, editor):
    """Create a recipe in the working dir from a neutral stats plot spec.

    Body: ``{"spec": <scitex-stats.plot-spec>, "name": optional stem}``. The
    workspace comes from the request (a host injects the user's project dir as
    ``?working_dir=``), never from a live editor, so the figure lands in the
    caller's project even when no recipe is open.
    """
    import re

    import matplotlib.pyplot as plt

    from figrecipe import save
    from figrecipe._integrations._stats_plot_spec import (
        from_stats_plot_spec,
        validate_stats_plot_spec,
    )

    from ._files_tree import _get_working_dir_and_backend

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid JSON body"}, status=400)
    spec = data.get("spec", data) if isinstance(data, dict) else None
    try:
        validate_stats_plot_spec(spec)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    working_dir, files = _get_working_dir_and_backend(request, None)
    raw = str(data.get("name") or f"stats_{spec.get('test', {}).get('key', 'plot')}")
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")[:60] or "stats_plot"
    counter = 1
    while files.exists(f"{stem}_{counter:03d}.yaml"):
        counter += 1
    rel = f"{stem}_{counter:03d}.yaml"
    target = Path(working_dir) / rel

    fig, _ax = from_stats_plot_spec(spec)
    try:
        save(fig, target.with_suffix(".png"), validate=False, verbose=False)
    finally:
        plt.close(getattr(fig, "_fig", fig))
    return JsonResponse(
        {
            "success": True,
            "file": rel,
            "recipe_path": str(target),
            "working_dir": str(working_dir),
        }
    )


def handle_stats_list_brackets(request, editor):
    """List all statistical brackets on the figure."""
    from figrecipe._annotations import list_stat_brackets

    ax_index = int(request.GET.get("ax_index", -1))

    try:
        fig = editor.fig
        axes_list = fig.get_axes()
        result = {}

        if ax_index >= 0:
            if ax_index >= len(axes_list):
                return JsonResponse(
                    {"error": f"Invalid axis index: {ax_index}"}, status=400
                )
            result[str(ax_index)] = list_stat_brackets(axes_list[ax_index])
        else:
            for i, ax in enumerate(axes_list):
                brackets = list_stat_brackets(ax)
                if brackets:
                    result[str(i)] = brackets

        return JsonResponse({"brackets": result})

    except Exception as e:
        logger.exception("[FigRecipe] stats/list_brackets failed")
        return JsonResponse({"error": str(e)}, status=500)
