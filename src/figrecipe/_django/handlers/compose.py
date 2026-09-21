#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compose handlers: compose canvas figures into a single output.

Uses PIL image composition to paste rendered preview images at their
exact canvas positions. This guarantees pixel-perfect output matching
the canvas layout, including theme, dark mode, and all decorations.
"""

import base64
import io
import json
from pathlib import Path

import scitex_logging as slogging

from ..._utils._optional import missing_extra

try:
    from django.http import HttpResponse, JsonResponse
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

logger = slogging.getLogger(__name__)


def _parse_figures(request):
    """Parse placed figures from request body.

    Returns (figures, dark_mode, working_dir).
    Each figure: {path, x, y, width, height, image (base64)}.
    """
    data = json.loads(request.body) if request.body else {}
    figures = data.get("figures", [])
    dark_mode = data.get("dark_mode", False)
    working_dir = data.get("working_dir", "")

    if not figures:
        raise ValueError("No figures on canvas")

    for fig in figures:
        logger.info(
            "[Compose] Figure '%s': x=%d, y=%d, w=%d, h=%d, has_image=%s",
            fig.get("path", "?"),
            fig.get("x", 0),
            fig.get("y", 0),
            fig.get("width", 0),
            fig.get("height", 0),
            bool(fig.get("image")),
        )

    return figures, dark_mode, working_dir


def _compose_pil(figures, dark_mode):
    """Compose figures into a single PIL Image by pasting at canvas positions.

    Each figure has {x, y, width, height, image} where image is base64 PNG.
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    # Compute canvas bounds from figure positions + sizes
    max_x = 0
    max_y = 0
    for fig in figures:
        right = int(fig["x"]) + int(fig["width"])
        bottom = int(fig["y"]) + int(fig["height"])
        max_x = max(max_x, right)
        max_y = max(max_y, bottom)

    canvas_w = max_x + 4  # small margin
    canvas_h = max_y + 4

    logger.info("[Compose] Canvas: %d x %d px", canvas_w, canvas_h)

    # Create canvas with appropriate background
    bg = (30, 30, 30, 255) if dark_mode else (255, 255, 255, 255)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), bg)

    # Paste each figure at its position
    for fig in figures:
        img_b64 = fig.get("image", "")
        if not img_b64:
            logger.warning(
                "[Compose] Figure '%s' has no image data, skipping", fig.get("path")
            )
            continue

        img_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")

        # Resize to match the exact canvas dimensions
        target_w = int(fig["width"])
        target_h = int(fig["height"])
        if img.size != (target_w, target_h):
            img = img.resize((target_w, target_h), Image.LANCZOS)

        x = int(fig["x"])
        y = int(fig["y"])
        canvas.paste(img, (x, y), img)  # use alpha mask

        # Draw panel letter (A, B, C...) — Arial 10pt bold
        panel_letter = fig.get("panel_letter")
        if panel_letter:
            try:
                from PIL import ImageDraw, ImageFont
            except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
                raise missing_extra(exc) from exc

            draw = ImageDraw.Draw(canvas)
            # 10pt at 300 DPI = 10 * 300/72 ≈ 42px
            font_size = round(10 * 300 / 72)
            for font_name in (
                "Arial-Bold",
                "Arial Bold",
                "arial",
                "DejaVuSans-Bold",
                "LiberationSans-Bold",
            ):
                try:
                    font = ImageFont.truetype(f"{font_name}.ttf", font_size)
                    break
                except (OSError, IOError):
                    continue
            else:
                font = ImageFont.load_default()

            # Respect custom position if provided
            lpos = fig.get("panel_letter_pos")
            lx = int(lpos["x"]) if lpos else 8
            ly = int(lpos["y"]) if lpos else 6

            # Plain bold text, no background (publication style)
            text_color = (255, 255, 255, 255) if dark_mode else (0, 0, 0, 255)
            draw.text(
                (x + lx, y + ly),
                panel_letter,
                fill=text_color,
                font=font,
            )

    return canvas


def handle_compose_save(request, editor):
    """Compose canvas figures and save as PNG."""
    figures, dark_mode, working_dir = _parse_figures(request)
    canvas = _compose_pil(figures, dark_mode)

    # Determine output path
    data = json.loads(request.body) if request.body else {}
    filename = data.get("filename", "composed")

    if working_dir:
        out_dir = Path(working_dir)
    elif editor and editor.recipe_path:
        out_dir = editor.recipe_path.parent
    else:
        out_dir = Path(".")

    out_path = out_dir / f"{filename}.png"

    # Save as PNG
    canvas_rgb = canvas.convert("RGB")
    canvas_rgb.save(str(out_path), "PNG", dpi=(300, 300))
    logger.info("[Compose] Saved to %s (%dx%d)", out_path, canvas.width, canvas.height)

    return JsonResponse(
        {
            "success": True,
            "path": str(out_path),
        }
    )


def handle_compose_export(request, editor, fmt):
    """Compose canvas figures and return as downloadable blob."""
    fmt = fmt.lower()
    if fmt not in ("png", "svg", "pdf"):
        return JsonResponse({"error": f"Unsupported format: {fmt}"}, status=400)

    figures, dark_mode, working_dir = _parse_figures(request)
    canvas = _compose_pil(figures, dark_mode)

    data = json.loads(request.body) if request.body else {}
    filename = data.get("filename", "composed")

    buf = io.BytesIO()
    if fmt == "png":
        canvas.convert("RGB").save(buf, "PNG", dpi=(300, 300))
        mimetype = "image/png"
    elif fmt == "pdf":
        canvas.convert("RGB").save(buf, "PDF", resolution=300)
        mimetype = "application/pdf"
    elif fmt == "svg":
        # SVG from raster: embed as base64 image in SVG wrapper
        png_buf = io.BytesIO()
        canvas.convert("RGB").save(png_buf, "PNG", dpi=(300, 300))
        png_b64 = base64.b64encode(png_buf.getvalue()).decode()
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{canvas.width}" height="{canvas.height}">'
            f'<image href="data:image/png;base64,{png_b64}" '
            f'width="{canvas.width}" height="{canvas.height}"/>'
            f"</svg>"
        )
        buf.write(svg.encode())
        mimetype = "image/svg+xml"
    buf.seek(0)

    response = HttpResponse(buf.read(), content_type=mimetype)
    response["Content-Disposition"] = f'attachment; filename="{filename}.{fmt}"'
    return response
