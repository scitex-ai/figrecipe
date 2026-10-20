#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hitmap generation for diagram elements.

Renders each diagram element (box, container, arrow) with a unique solid
RGB color on a clean canvas.  The resulting image + color_map dict enable
pixel-based element identification for GUI editors.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ..._utils._optional import missing_extra

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

if TYPE_CHECKING:
    from ._core import Diagram


def _id_to_rgb(element_id: int) -> Tuple[int, int, int]:
    """Map element ID (1-based) to a unique RGB color.

    Uses deterministic HSV spacing so nearby IDs are visually distinct.
    ID 0 is reserved for background (white).
    """
    if element_id <= 0:
        return (255, 255, 255)
    # 12 hand-picked distinct colors, then HSV-generated
    _PALETTE = [
        (255, 0, 0),
        (0, 200, 0),
        (0, 0, 255),
        (255, 200, 0),
        (255, 0, 200),
        (0, 200, 200),
        (200, 100, 0),
        (100, 0, 200),
        (0, 100, 50),
        (200, 0, 100),
        (100, 200, 0),
        (0, 100, 200),
    ]
    if element_id <= len(_PALETTE):
        return _PALETTE[element_id - 1]
    import colorsys

    hue = ((element_id - 1) * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
    return (int(r * 255), int(g * 255), int(b * 255))


def _rgb_norm(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Normalize 0-255 RGB to 0-1 for matplotlib."""
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def generate_diagram_hitmap(
    diagram: "Diagram",
    dpi: int = 150,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Generate a hitmap image for a rendered diagram.

    Each box, container, and arrow is drawn with a unique solid color
    on a white background.

    Parameters
    ----------
    diagram : Diagram
        A diagram that has been finalized (positions resolved).
    dpi : int
        Resolution for the hitmap image.

    Returns
    -------
    hitmap : PIL.Image.Image
        RGB image where each element has a unique color.
    color_map : dict
        Mapping from element_id to metadata::

            {"box:core": {"id": 1, "type": "box", "rgb": [255, 0, 0]}, ...}
    """

    color_map: Dict[str, Dict[str, Any]] = {}
    eid = 1

    # Create a clean figure matching the diagram canvas
    figsize = (
        (diagram.xlim[1] - diagram.xlim[0]) / 25.4,
        (diagram.ylim[1] - diagram.ylim[0]) / 25.4,
    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(diagram.xlim)
    ax.set_ylim(diagram.ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Draw containers as solid color rectangles
    for cid in diagram._containers:
        if cid not in diagram._positions:
            continue
        pos = diagram._positions[cid]
        rgb = _id_to_rgb(eid)
        patch = FancyBboxPatch(
            (pos.x_mm - pos.width_mm / 2, pos.y_mm - pos.height_mm / 2),
            pos.width_mm,
            pos.height_mm,
            boxstyle="round,pad=1.0,rounding_size=3.0",
            facecolor=_rgb_norm(rgb),
            edgecolor=_rgb_norm(rgb),
            linewidth=2.5,
            zorder=1,
        )
        ax.add_patch(patch)
        color_map[f"container:{cid}"] = {
            "id": eid,
            "type": "container",
            "rgb": list(rgb),
            "title": diagram._containers[cid].get("title"),
        }
        eid += 1

    # Draw boxes as solid color rectangles
    for bid, box in diagram._boxes.items():
        if bid not in diagram._positions:
            continue
        pos = diagram._positions[bid]
        rgb = _id_to_rgb(eid)
        patch = FancyBboxPatch(
            (pos.x_mm - pos.width_mm / 2, pos.y_mm - pos.height_mm / 2),
            pos.width_mm,
            pos.height_mm,
            boxstyle="round,pad=1.0,rounding_size=2.0",
            facecolor=_rgb_norm(rgb),
            edgecolor=_rgb_norm(rgb),
            linewidth=2,
            zorder=2,
        )
        ax.add_patch(patch)
        color_map[f"box:{bid}"] = {
            "id": eid,
            "type": "box",
            "rgb": list(rgb),
            "title": box.title,
        }
        eid += 1

    # Draw arrows as colored lines
    for arrow in diagram._arrows:
        src_pos = diagram._positions.get(arrow.source)
        tgt_pos = diagram._positions.get(arrow.target)
        if not src_pos or not tgt_pos:
            continue
        if arrow.source_anchor == "auto" or arrow.target_anchor == "auto":
            sa, ta = diagram._auto_anchor(src_pos, tgt_pos)
        else:
            sa, ta = arrow.source_anchor, arrow.target_anchor
        start = diagram._get_anchor(src_pos, sa)
        end = diagram._get_anchor(tgt_pos, ta)
        rgb = _id_to_rgb(eid)
        conn = f"arc3,rad={arrow.curve}" if arrow.curve else "arc3,rad=0"
        patch = FancyArrowPatch(
            posA=start,
            posB=end,
            arrowstyle="-|>",
            color=_rgb_norm(rgb),
            linewidth=4,  # thicker for easier clicking
            connectionstyle=conn,
            mutation_scale=15,
            zorder=5,
        )
        ax.add_patch(patch)
        color_map[f"arrow:{arrow.source}->{arrow.target}"] = {
            "id": eid,
            "type": "arrow",
            "rgb": list(rgb),
            "source": arrow.source,
            "target": arrow.target,
        }
        eid += 1

    # Render to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    hitmap = Image.open(buf).convert("RGB")
    plt.close(fig)

    return hitmap, color_map


def save_diagram_hitmap(
    diagram: "Diagram",
    path: Path,
    dpi: int = 150,
) -> Path:
    """Generate and save diagram hitmap alongside a color_map JSON.

    Parameters
    ----------
    diagram : Diagram
        Finalized diagram.
    path : Path
        Output path for the hitmap PNG (e.g. workflow_hitmap.png).
        A .json sidecar with the color_map is saved alongside.
    dpi : int
        Resolution.

    Returns
    -------
    Path
        Path to saved hitmap PNG.
    """
    path = Path(path)
    hitmap, color_map = generate_diagram_hitmap(diagram, dpi=dpi)
    path.parent.mkdir(parents=True, exist_ok=True)
    hitmap.save(str(path))
    json_path = path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(color_map, f, indent=2)
    return path


__all__ = ["generate_diagram_hitmap", "save_diagram_hitmap"]
