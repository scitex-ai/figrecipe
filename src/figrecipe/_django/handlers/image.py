#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image drop handlers: add_image_panel, add_image_from_url, load_recipe."""

import base64
import io
import urllib.request

import scitex_logging as slogging

from ..._utils._optional import missing_extra

try:
    from django.http import JsonResponse
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

logger = slogging.getLogger(__name__)


def _add_image_panel(editor, img_array, filename, drop_x, drop_y):
    """Add a new imshow panel at the drop position."""
    from figrecipe._wrappers._axes import RecordingAxes

    fig = editor.fig
    panel_width, panel_height = 0.4, 0.4
    left = max(0.05, min(0.55, drop_x - panel_width / 2))
    bottom = max(0.05, min(0.55, (1 - drop_y) - panel_height / 2))

    mpl_ax = fig.add_axes([left, bottom, panel_width, panel_height])

    if hasattr(fig, "_recorder"):
        recorder = fig._recorder
        existing = len(fig.get_axes()) - 1
        wrapped_ax = RecordingAxes(mpl_ax, recorder, position=(existing, 0))
        wrapped_ax.imshow(img_array, id=f"dropped_{filename[:15]}")
        wrapped_ax.set_title(filename[:20])
        wrapped_ax.axis("off")
        if hasattr(fig, "_axes"):
            fig._axes.append([wrapped_ax])
    else:
        mpl_ax.imshow(img_array)
        mpl_ax.set_title(filename[:20])
        mpl_ax.axis("off")


def _render_after_image(editor):
    """Re-render and regenerate hitmap after image panel addition."""
    from figrecipe._editor._helpers import render_with_overrides

    from .core import _regen_hitmap

    img, bboxes, size = render_with_overrides(
        editor.fig, editor.get_effective_style(), editor.dark_mode
    )
    _regen_hitmap(editor, size)
    return JsonResponse(
        {
            "success": True,
            "image": img,
            "bboxes": bboxes,
            "img_size": {"width": size[0], "height": size[1]},
        }
    )


def handle_add_image_panel(request, editor):
    """POST /add_image_panel -- add a new panel from a base64-encoded image."""
    import json

    import numpy as np
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    data = json.loads(request.body) if request.body else {}
    image_data = data.get("image_data")
    filename = data.get("filename", "dropped_image")
    drop_x = data.get("drop_x", 0.5)
    drop_y = data.get("drop_y", 0.5)

    if not image_data:
        return JsonResponse({"error": "Missing image_data"}, status=400)

    try:
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        _add_image_panel(editor, img_array, filename, drop_x, drop_y)
        return _render_after_image(editor)
    except Exception as e:
        logger.exception("[FigRecipe] add_image_panel failed")
        return JsonResponse({"error": f"Failed to add image: {e}"}, status=500)


def handle_add_image_from_url(request, editor):
    """POST /add_image_from_url -- add a new panel from an image URL."""
    import json

    import numpy as np
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    data = json.loads(request.body) if request.body else {}
    url = data.get("url")
    drop_x = data.get("drop_x", 0.5)
    drop_y = data.get("drop_y", 0.5)

    if not url:
        return JsonResponse({"error": "Missing url"}, status=400)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            image_bytes = response.read()
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        filename = url.split("/")[-1].split("?")[0][:20]
        _add_image_panel(editor, img_array, filename, drop_x, drop_y)
        return _render_after_image(editor)
    except Exception as e:
        logger.exception("[FigRecipe] add_image_from_url failed")
        return JsonResponse({"error": f"Failed to add image from URL: {e}"}, status=500)


def handle_load_recipe(request, editor):
    """POST /load_recipe -- replace current figure by reproducing a dropped recipe."""
    import json
    import tempfile

    import figrecipe as fr

    data = json.loads(request.body) if request.body else {}
    recipe_content = data.get("recipe_content")
    filename = data.get("filename", "recipe.yaml")

    if not recipe_content:
        return JsonResponse({"error": "Missing recipe_content"}, status=400)

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(recipe_content)
            temp_path = f.name

        fig, _ = fr.reproduce(temp_path)
        editor.fig = fig
        editor._hitmap_generated = False
        editor._color_map = {}
        return JsonResponse({"success": True, "message": f"Loaded {filename}"})
    except Exception as e:
        logger.exception("[FigRecipe] load_recipe failed")
        return JsonResponse({"error": f"Failed to load recipe: {e}"}, status=500)
