#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download handlers: download CSV, download figure."""


from ..._utils._optional import missing_extra

try:
    import scitex_logging as slogging
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


try:
    from django.http import HttpResponse, JsonResponse
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

logger = slogging.getLogger(__name__)


def handle_download_csv(request, editor):
    """Download plotted data as CSV."""
    from figrecipe._api._extract import csv_bytes_from_record

    fig = editor.fig
    if not hasattr(fig, "record") or fig.record is None:
        return JsonResponse({"error": "No recorded data available"}, status=400)

    csv_bytes = csv_bytes_from_record(fig.record)
    if csv_bytes is None:
        return JsonResponse({"error": "No plot data found"}, status=400)

    filename = "figure_data.csv"
    if editor.recipe_path:
        filename = f"{editor.recipe_path.stem}_data.csv"

    response = HttpResponse(csv_bytes, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def handle_download_fig(request, editor, fmt):
    """Download figure as png/svg/pdf at 300 DPI."""
    from figrecipe._editor._renderer import render_download

    fmt = fmt.lower()
    if fmt not in ("png", "svg", "pdf"):
        return JsonResponse({"error": f"Unsupported format: {fmt}"}, status=400)

    effective_style = editor.get_effective_style()
    content = render_download(
        editor.fig,
        fmt=fmt,
        dpi=300,
        overrides=effective_style if effective_style else None,
        dark_mode=False,
    )

    mimetype = {
        "png": "image/png",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }[fmt]
    filename = f"figure.{fmt}"
    if editor.recipe_path:
        filename = f"{editor.recipe_path.stem}.{fmt}"

    response = HttpResponse(content, content_type=mimetype)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
