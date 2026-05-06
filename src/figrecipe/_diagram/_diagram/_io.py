#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serialization and deserialization for Diagram diagrams."""

from typing import TYPE_CHECKING, Any, Dict

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ._core import Diagram


def diagram_to_dict(info: "Diagram") -> Dict[str, Any]:
    """Convert diagram specification to dictionary for serialization.

    Parameters
    ----------
    info : Diagram
        The diagram to serialize.

    Returns
    -------
    dict
        Dictionary representation suitable for YAML recipe.
    """
    return {
        "title": info.title,
        "width_mm": info.width_mm,
        "height_mm": info.height_mm,
        "xlim": list(info.xlim),
        "ylim": list(info.ylim),
        "boxes": [
            {
                "id": box.id,
                "title": box.title,
                "subtitle": box.subtitle,
                "content": box.content,
                "emphasis": box.emphasis,
                "shape": box.shape,
                "fill_color": box.fill_color,
                "border_color": box.border_color,
                "title_color": box.title_color,
                "padding_mm": box.padding_mm,
                "margin_mm": box.margin_mm,
            }
            for box in info._boxes.values()
        ],
        "containers": [
            {
                "id": cid,
                "title": cont.get("title"),
                "children": cont.get("children", []),
                "emphasis": cont.get("emphasis", "muted"),
                "fill_color": cont.get("fill_color"),
                "border_color": cont.get("border_color"),
                "direction": cont.get("direction", "row"),
                "gap_mm": cont.get("gap_mm", 8.0),
                "padding_mm": cont.get("padding_mm", 8.0),
            }
            for cid, cont in info._containers.items()
        ],
        "arrows": [
            {
                "source": arrow.source,
                "target": arrow.target,
                "source_anchor": arrow.source_anchor,
                "target_anchor": arrow.target_anchor,
                "label": arrow.label,
                "style": arrow.style,
                "color": arrow.color,
                "curve": arrow.curve,
                "linewidth_mm": arrow.linewidth_mm,
            }
            for arrow in info._arrows
        ],
        "positions": {
            pid: {
                "x_mm": pos.x_mm,
                "y_mm": pos.y_mm,
                "width_mm": pos.width_mm,
                "height_mm": pos.height_mm,
            }
            for pid, pos in info._positions.items()
        },
    }


def diagram_from_dict(data: Dict[str, Any]) -> "Diagram":
    """Create Diagram from dictionary (recipe reproduction).

    Parameters
    ----------
    data : dict
        Dictionary from to_dict() or YAML recipe.

    Returns
    -------
    Diagram
        Reconstructed diagram.
    """
    from ._core import ArrowSpec, BoxSpec, Diagram, PositionSpec

    width_mm = data.get("width_mm", 200.0)
    height_mm = data.get("height_mm", 120.0)

    diagram = Diagram(
        title=data.get("title"),
        width_mm=width_mm,
        height_mm=height_mm,
    )

    # Restore expanded limits if available (auto_layout may have expanded them)
    if "xlim" in data:
        diagram.xlim = tuple(data["xlim"])
    if "ylim" in data:
        diagram.ylim = tuple(data["ylim"])

    # Restore positions first
    for pid, pos in data.get("positions", {}).items():
        diagram._positions[pid] = PositionSpec(
            x_mm=pos.get("x_mm", 0.0),
            y_mm=pos.get("y_mm", 0.0),
            width_mm=pos.get("width_mm", 0.0),
            height_mm=pos.get("height_mm", 0.0),
        )

    # Restore boxes
    for box_data in data.get("boxes", []):
        diagram._boxes[box_data["id"]] = BoxSpec(
            id=box_data["id"],
            title=box_data["title"],
            subtitle=box_data.get("subtitle"),
            content=box_data.get("content", []),
            emphasis=box_data.get("emphasis", "normal"),
            shape=box_data.get("shape", "rounded"),
            fill_color=box_data.get("fill_color"),
            border_color=box_data.get("border_color"),
            title_color=box_data.get("title_color"),
            padding_mm=box_data.get("padding_mm", 5.0),
            margin_mm=box_data.get("margin_mm", 0.0),
        )

    # Restore containers
    for cont_data in data.get("containers", []):
        diagram._containers[cont_data["id"]] = {
            "title": cont_data.get("title"),
            "children": cont_data.get("children", []),
            "emphasis": cont_data.get("emphasis", "muted"),
            "fill_color": cont_data.get("fill_color"),
            "border_color": cont_data.get("border_color"),
            "direction": cont_data.get("direction", "row"),
            "gap_mm": cont_data.get("gap_mm", 8.0),
            "padding_mm": cont_data.get("padding_mm", 8.0),
        }

    # Restore arrows
    for arrow_data in data.get("arrows", []):
        diagram._arrows.append(
            ArrowSpec(
                source=arrow_data["source"],
                target=arrow_data["target"],
                source_anchor=arrow_data.get("source_anchor", "auto"),
                target_anchor=arrow_data.get("target_anchor", "auto"),
                label=arrow_data.get("label"),
                style=arrow_data.get("style", "solid"),
                color=arrow_data.get("color"),
                curve=arrow_data.get("curve", 0.0),
                linewidth_mm=arrow_data.get("linewidth_mm", 0.5),
            )
        )

    return diagram


def save_diagram_recipe(
    diagram: "Diagram",
    path,
    dpi: int = 200,
):
    """Save a standalone YAML recipe for a Diagram.

    Parameters
    ----------
    diagram : Diagram
        The diagram to save.
    path : str or Path
        Output YAML path.
    dpi : int
        DPI used for rendering.

    Returns
    -------
    Path
        Path to saved YAML file.
    """
    import datetime
    from pathlib import Path

    import yaml

    path = Path(path)
    data = diagram_to_dict(diagram)

    recipe = {
        "figrecipe": "1.0",
        "type": "diagram",
        "created": datetime.datetime.now().isoformat(),
        "dpi": dpi,
        "diagram": data,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

    return path


def _add_watermark(path, dpi=200):
    """Stamp 'Plotted by {BRAND_NAME}' on bottom-right of a saved image."""
    from PIL import Image, ImageDraw, ImageFont

    from figrecipe._branding import BRAND_NAME

    img = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = max(8, int(7 * dpi / 72))  # 7pt → pixels
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()
    from figrecipe import __version__ as _version

    display = "FigRecipe" if BRAND_NAME == "figrecipe" else BRAND_NAME
    text = f"Plotted by {display} v{_version}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = img.width - tw - 8, img.height - th - 6
    draw.text((x, y), text, font=font, fill=(170, 170, 170, 217))  # alpha~0.85
    img = Image.alpha_composite(img, overlay).convert("RGB")
    img.save(path)
    logger.info("watermark added: '%s' (%dpx font at %d DPI)", text, font_size, dpi)


def _render_to_file(
    diagram: "Diagram",
    path,
    dpi: int = 200,
    save_recipe: bool = True,
    save_hitmap: bool = True,
    save_debug: bool = True,
    watermark: bool = False,
):
    """Render diagram and save to file. On validation failure, saves as *_FAILED.png.

    Post-processing crop strategy (no bbox_inches='tight'):
    - Raster formats: pixel-based content-aware crop via figrecipe._utils._crop.crop
    - SVG: viewBox adjustment via crop_svg, triggered automatically by the
      patched fig.savefig installed in Diagram.render()
    """
    from pathlib import Path

    import matplotlib.pyplot as plt

    path = Path(path)
    fig, ax = diagram.render()
    if fig._figrecipe_diagram_failed:
        path = path.with_stem(f"{path.stem}_FAILED")

    # Save without bbox_inches='tight' — post-processing crop handles whitespace
    fig.savefig(path, dpi=dpi, facecolor="white")

    # Raster: pixel-based content-aware crop (SVG is handled by patched savefig)
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}:
        from figrecipe._utils._crop import crop

        crop(path, output_path=path, margin_mm=1.0, overwrite=True, verbose=False)

    if watermark:
        _add_watermark(path, dpi=dpi)
    if save_recipe and not fig._figrecipe_diagram_failed:
        save_diagram_recipe(diagram, path.with_suffix(".yaml"), dpi=dpi)
    if save_hitmap:
        from ._hitmap import save_diagram_hitmap

        save_diagram_hitmap(diagram, path.with_stem(path.stem + "_hitmap"), dpi=dpi)
    if save_debug:
        from ._debug import generate_debug_image

        debug_fig = generate_debug_image(diagram, dpi=dpi)
        debug_path = path.with_stem(path.stem + "_debug")
        # Debug figure: plain save + post-processing crop
        debug_fig.savefig(debug_path, dpi=dpi, facecolor="white")
        if debug_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            from figrecipe._utils._crop import crop

            crop(
                debug_path,
                output_path=debug_path,
                margin_mm=1.0,
                overwrite=True,
                verbose=False,
            )
        plt.close(debug_fig)
    plt.close(fig)
    try:
        from PIL import Image

        w, h = Image.open(path).size
        w_mm, h_mm = w / dpi * 25.4, h / dpi * 25.4
        _log = getattr(logger, "success", logger.info)
        _log("diagram saved: %s [W: %.1fmm, H: %.1fmm]", path.name, w_mm, h_mm)
    except Exception:
        pass
    return path


# Public backward-compat alias — prefer d.save() at call sites
render_to_file = _render_to_file

__all__ = [
    "diagram_to_dict",
    "diagram_from_dict",
    "save_diagram_recipe",
    "_render_to_file",
    "render_to_file",  # backward-compat alias
]
