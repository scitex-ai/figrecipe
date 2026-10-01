#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Element/call handlers: calls, update_call, update_element_color, element_details."""

import json
import re

from ..._utils._optional import missing_extra

try:
    import scitex_logging as slogging
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


try:
    from django.http import JsonResponse
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

logger = slogging.getLogger(__name__)

# Hitmap element key: ax{axes_index}_{kind}{artist_index}, e.g. ax0_bar3,
# ax2_image0, ax1_boxplot_box0. The kind itself may carry underscores.
_ELEMENT_KEY_RE = re.compile(r"^ax(\d+)_(.*?)(\d+)$")


def _num(value):
    """Plain float for numpy scalars, else the value unchanged."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _get_call_id(call):
    return getattr(call, "id", None) or getattr(call, "call_id", None)


def handle_calls(request, editor):
    from figrecipe._editor._helpers import to_json_serializable

    if not hasattr(editor.fig, "record") or not editor.fig.record:
        return JsonResponse({})

    calls = {}
    for ax_key, ax_record in editor.fig.record.axes.items():
        for call in getattr(ax_record, "calls", []):
            cid = _get_call_id(call) or f"{ax_key}_{id(call)}"
            try:
                from figrecipe._signatures import get_signature

                sig = get_signature(getattr(call, "function", ""))
            except Exception:
                sig = {}

            calls[cid] = to_json_serializable(
                {
                    "function": getattr(call, "function", "unknown"),
                    "ax_key": ax_key,
                    "args": getattr(call, "args", []),
                    "kwargs": getattr(call, "kwargs", {}),
                    "signature": {
                        "args": sig.get("args", []),
                        "kwargs": {
                            k: v
                            for k, v in sig.get("kwargs", {}).items()
                            if k != "**kwargs"
                        },
                    },
                }
            )
    return JsonResponse(calls)


def handle_single_call(request, editor, call_id):
    """GET /call/<call_id> -- get one recorded call's data."""
    from figrecipe._editor._helpers import to_json_serializable

    if hasattr(editor.fig, "record"):
        for ax_key, ax_record in editor.fig.record.axes.items():
            for call in getattr(ax_record, "calls", []):
                if _get_call_id(call) == call_id:
                    try:
                        from figrecipe._signatures import get_signature

                        sig = get_signature(getattr(call, "function", ""))
                    except Exception:
                        sig = {}

                    return JsonResponse(
                        {
                            "call_id": call_id,
                            "function": getattr(call, "function", "unknown"),
                            "ax_key": ax_key,
                            "args": to_json_serializable(getattr(call, "args", [])),
                            "kwargs": to_json_serializable(getattr(call, "kwargs", {})),
                            "signature": {
                                "args": sig.get("args", []),
                                "kwargs": {
                                    k: v
                                    for k, v in sig.get("kwargs", {}).items()
                                    if k != "**kwargs"
                                },
                            },
                        }
                    )

    return JsonResponse({"error": f"Call {call_id} not found"}, status=404)


def handle_update_call(request, editor):
    """POST /update_call -- change a call parameter and re-render."""
    from figrecipe._editor._helpers import render_with_overrides, to_json_serializable

    from .core import _regen_hitmap

    data = json.loads(request.body) if request.body else {}
    call_id = data.get("call_id")
    param = data.get("param")
    value = data.get("value")

    if not call_id or not param:
        return JsonResponse({"error": "Missing call_id or param"}, status=400)

    updated = False
    if hasattr(editor.fig, "record"):
        for ax_key, ax_record in editor.fig.record.axes.items():
            for call in getattr(ax_record, "calls", []):
                if _get_call_id(call) == call_id:
                    editor.style_overrides.set_call_override(call_id, param, value)

                    is_diagram = getattr(call, "function", "") in (
                        "diagram",
                        "schematic",
                    )
                    if not is_diagram:
                        if value is None or value == "" or value == "null":
                            call.kwargs.pop(param, None)
                        else:
                            call.kwargs[param] = value

                    updated = True
                    break
            if updated:
                break

    if not updated:
        return JsonResponse({"error": f"Call {call_id} not found"}, status=404)

    if editor.recipe_path and hasattr(editor.fig, "save_recipe"):
        try:
            editor.fig.save_recipe(editor.recipe_path)
        except Exception as save_err:
            logger.warning("[FigRecipe] Auto-save failed: %s", save_err)

    try:
        img, bboxes, size = render_with_overrides(
            editor.fig, editor.get_effective_style(), editor.dark_mode
        )
        _regen_hitmap(editor, size)
    except Exception as e:
        logger.exception("[FigRecipe] update_call re-render failed")
        return JsonResponse({"error": f"Re-render failed: {str(e)}"}, status=500)

    updated_call = None
    if hasattr(editor.fig, "record"):
        for ax_key, ax_record in editor.fig.record.axes.items():
            for call in getattr(ax_record, "calls", []):
                if _get_call_id(call) == call_id:
                    updated_call = {"kwargs": to_json_serializable(call.kwargs)}
                    break
            if updated_call:
                break

    return JsonResponse(
        {
            "success": True,
            "image": img,
            "bboxes": bboxes,
            "img_size": {"width": size[0], "height": size[1]},
            "call_id": call_id,
            "param": param,
            "value": value,
            "has_call_overrides": editor.style_overrides.has_call_overrides(),
            "updated_call": updated_call,
        }
    )


def handle_update_element_color(request, editor):
    """POST /update_element_color -- direct color edit for un-recorded elements."""
    from figrecipe._editor._helpers import render_with_overrides

    from .core import _regen_hitmap

    data = json.loads(request.body) if request.body else {}
    element_key = data.get("element_key")
    color = data.get("color")
    ax_index = data.get("ax_index")
    element_type = data.get("element_type")
    layer_index = data.get("layer_index")

    if not element_key or not color:
        return JsonResponse({"error": "Missing element_key or color"}, status=400)

    try:
        fig = editor.fig
        axes = fig.get_axes()

        if ax_index is not None and ax_index < len(axes):
            ax = axes[ax_index]
            updated = False

            if "scatter" in element_key or element_type == "scatter":
                from matplotlib.collections import PathCollection

                for coll in ax.collections:
                    if isinstance(coll, PathCollection):
                        coll.set_facecolors([color])
                        coll.set_edgecolors([color])
                        updated = True
                        break

            elif "line" in element_key or element_type in ("line", "step"):
                for line in ax.get_lines():
                    if line.get_visible():
                        line.set_color(color)
                        line.set_markerfacecolor(color)
                        line.set_markeredgecolor(color)
                        updated = True
                        break

            elif "stackplot" in element_key or element_type == "stackplot":
                from matplotlib.collections import PolyCollection

                poly_idx = 0
                for coll in ax.collections:
                    if isinstance(coll, PolyCollection):
                        if layer_index is None or poly_idx == layer_index:
                            coll.set_facecolors([color])
                            coll.set_edgecolors([color])
                            updated = True
                            if layer_index is not None:
                                break
                        poly_idx += 1

            elif "fill" in element_key or element_type == "fill":
                from matplotlib.collections import PolyCollection

                for coll in ax.collections:
                    if isinstance(coll, PolyCollection):
                        coll.set_facecolors([color])
                        coll.set_edgecolors([color])
                        updated = True
                        break

            elif "bar" in element_key or element_type == "bar":
                for patch in ax.patches:
                    patch.set_facecolor(color)
                    patch.set_edgecolor(color)
                    updated = True

            if not updated:
                return JsonResponse(
                    {"error": f"Could not find element: {element_key}"}, status=404
                )

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
    except Exception as e:
        logger.exception("[FigRecipe] update_element_color failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_element_details(request, editor):
    """GET /element_details?element=<hitmap key>[&row=&col=][&index=].

    Inspect one canvas element the hitmap hit-tested: bars report their
    value and position, matrix images (imshow/matshow/pcolormesh) report
    the cell value at ``row``/``col`` plus the matrix shape and range, and
    scatter/line series report the point at ``index`` (or the series
    summary without it). Series identity comes from the hitmap color map,
    values from the live artists — so the panel shows what the click hit,
    not a re-guess from the recipe.
    """
    from figrecipe._editor._helpers import to_json_serializable

    key = request.GET.get("element", "")
    match = _ELEMENT_KEY_RE.match(key or "")
    if not match:
        return JsonResponse(
            {"error": "Please select a canvas element first"}, status=400
        )
    ax_index, kind, artist_index = (
        int(match.group(1)),
        match.group(2),
        int(match.group(3)),
    )

    try:
        axes = editor.fig.get_axes()
    except Exception as e:
        return JsonResponse({"error": f"No figure loaded: {e}"}, status=400)
    if ax_index >= len(axes):
        return JsonResponse({"error": f"Unknown panel: {key}"}, status=404)
    ax = axes[ax_index]

    color_map = getattr(editor, "_color_map", None) or {}
    entry = color_map.get(key, {})
    details = {
        "element": key,
        "type": entry.get("type", kind),
        "label": entry.get("label", key),
        "ax_index": ax_index,
        "call_id": entry.get("call_id"),
        "series": entry.get("label", key),
    }

    def opt_int(name):
        try:
            raw = request.GET.get(name)
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    try:
        if kind in ("bar", "hist"):
            _bar_details(ax, artist_index, details)
        elif kind == "wedge":
            _wedge_details(ax, artist_index, details)
        elif kind == "scatter":
            _points_details(ax, artist_index, details, opt_int("index"), "scatter")
        elif kind in ("line", "step"):
            _line_details(ax, artist_index, details, opt_int("index"))
        elif kind == "image":
            _matrix_details(
                ax, artist_index, details, opt_int("row"), opt_int("col"), "image"
            )
        elif kind == "quadmesh":
            _matrix_details(
                ax, artist_index, details, opt_int("row"), opt_int("col"), "quadmesh"
            )
        elif kind == "contour":
            _contour_details(ax, artist_index, details)
    except (IndexError, ValueError):
        return JsonResponse({"error": f"Could not find element: {key}"}, status=404)
    return JsonResponse(to_json_serializable(details))


def _bar_details(ax, artist_index, details):
    """One Rectangle patch: value, position, and category label."""
    from matplotlib.patches import Rectangle

    # Hitmap bar keys carry the RAW ax.patches index (the key loop
    # enumerates every patch and skips the background/invisible without
    # renumbering) — resolve the same slot and validate it survived.
    patch = ax.patches[artist_index]
    if not isinstance(patch, Rectangle) or not patch.get_visible():
        raise IndexError(f"no bar at patches[{artist_index}]")
    x, y = patch.get_x(), patch.get_y()
    w, h = patch.get_width(), patch.get_height()
    horizontal = w > h
    value = x + w if horizontal else y + h
    pos = y + h / 2 if horizontal else x + w / 2
    details.update(
        {
            "value": _num(value),
            "position": _num(pos),
            "orientation": "horizontal" if horizontal else "vertical",
            "index": artist_index,
            "row": artist_index,
        }
    )
    labels = [t.get_text() for t in ax.get_xticklabels()]
    if (
        not horizontal
        and labels
        and artist_index < len(labels)
        and labels[artist_index]
    ):
        details["column"] = labels[artist_index]
    labels_y = [t.get_text() for t in ax.get_yticklabels()]
    if (
        horizontal
        and labels_y
        and artist_index < len(labels_y)
        and labels_y[artist_index]
    ):
        details["column"] = labels_y[artist_index]


def _wedge_details(ax, artist_index, details):
    """One pie slice: share of the whole."""
    from matplotlib.patches import Wedge

    # Raw ax.patches index, like the hitmap key loop.
    wedge = ax.patches[artist_index]
    if not isinstance(wedge, Wedge) or not wedge.get_visible():
        raise IndexError(f"no wedge at patches[{artist_index}]")
    span = wedge.theta2 - wedge.theta1
    details.update(
        {
            "value": _num(span / 360.0),
            "index": artist_index,
            "row": artist_index,
        }
    )


def _points_details(ax, artist_index, details, point_index, collection_kind):
    """One scatter collection: the point at ``index`` or the series summary."""
    from matplotlib.collections import PathCollection

    # Raw ax.collections index, like the hitmap key loop.
    coll = ax.collections[artist_index]
    if not isinstance(coll, PathCollection) or not coll.get_visible():
        raise IndexError(f"no scatter at collections[{artist_index}]")
    offsets = coll.get_offsets()
    label = coll.get_label()
    if label and not label.startswith("_"):
        details["series"] = label
    if point_index is not None:
        pt = offsets[point_index]
        details.update(
            {
                "value": [_num(pt[0]), _num(pt[1])],
                "index": point_index,
                "row": point_index,
            }
        )
    else:
        details.update(
            {
                "count": len(offsets),
                "x_range": [_num(min(offsets[:, 0])), _num(max(offsets[:, 0]))]
                if len(offsets)
                else None,
                "y_range": [_num(min(offsets[:, 1])), _num(max(offsets[:, 1]))]
                if len(offsets)
                else None,
            }
        )


def _line_details(ax, artist_index, details, point_index):
    """One line: the point at ``index`` or the series summary."""
    lines = ax.get_lines()
    line = lines[artist_index]
    if not line.get_visible():
        raise IndexError(f"no line at lines[{artist_index}]")
    label = line.get_label()
    if label and not label.startswith("_"):
        details["series"] = label
    xs, ys = list(line.get_xdata()), list(line.get_ydata())
    if point_index is not None:
        details.update(
            {
                "value": [_num(xs[point_index]), _num(ys[point_index])],
                "index": point_index,
                "row": point_index,
            }
        )
    else:
        details.update({"count": len(xs)})


def _matrix_details(ax, artist_index, details, row, col, image_kind):
    """One matrix image (imshow/matshow/pcolormesh cell grid): the cell value
    at ``row``/``col`` with row/column labels, plus shape and value range."""
    import numpy as np

    if image_kind == "image":
        from matplotlib.image import AxesImage

        # Raw ax.images index, like the hitmap key loop.
        artist = ax.images[artist_index]
        if not isinstance(artist, AxesImage) or not artist.get_visible():
            raise IndexError(f"no image at images[{artist_index}]")
        array = np.asarray(artist.get_array())
    else:
        from matplotlib.collections import QuadMesh

        # Raw ax.collections index, like the hitmap key loop.
        artist = ax.collections[artist_index]
        if not isinstance(artist, QuadMesh) or not artist.get_visible():
            raise IndexError(f"no mesh at collections[{artist_index}]")
        array = np.asarray(artist.get_array())
    array = np.asarray(array, dtype=float).reshape(array.shape[:2])
    n_rows, n_cols = array.shape
    details.update(
        {
            "shape": [n_rows, n_cols],
            "minimum": _num(np.nanmin(array)),
            "maximum": _num(np.nanmax(array)),
            "mean": _num(np.nanmean(array)),
        }
    )
    x_labels = [t.get_text() for t in ax.get_xticklabels()]
    y_labels = [t.get_text() for t in ax.get_yticklabels()]
    if x_labels and len(x_labels) == n_cols:
        details["column_labels"] = x_labels
    if y_labels and len(y_labels) == n_rows:
        details["row_labels"] = y_labels
    if row is not None and col is not None:
        if not (0 <= row < n_rows and 0 <= col < n_cols):
            raise IndexError(f"cell ({row}, {col}) outside {n_rows}x{n_cols}")
        details.update(
            {
                "value": _num(array[row, col]),
                "row": row,
                "col": col,
            }
        )
        if "column_labels" in details:
            details["column"] = details["column_labels"][col]
        else:
            details["column"] = col
        if "row_labels" in details:
            # y tick labels run bottom-up while matrix row 0 is the top.
            details["row_label"] = details["row_labels"][n_rows - 1 - row]
        else:
            details["row_label"] = row


def _contour_details(ax, artist_index, details):
    """One contour set: its levels."""
    from matplotlib.contour import QuadContourSet

    # Raw ax.collections index, like the hitmap key loop.
    artist = ax.collections[artist_index]
    if not isinstance(artist, QuadContourSet):
        raise IndexError(f"no contour at collections[{artist_index}]")
    levels = list(artist.levels)
    details.update(
        {
            "levels": [_num(v) for v in levels],
            "count": len(levels),
        }
    )
