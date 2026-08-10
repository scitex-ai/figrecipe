#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Views for the figrecipe editor Django app."""

import json
import logging
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .handlers import (
    HANDLERS,
    handle_download_fig,
    handle_single_call,
)
from .services import get_or_create_editor

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent / "static" / "figrecipe"


def _welcome_page(message: str) -> str:
    """Return a simple welcome/error page when no recipe is loaded."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>FigRecipe Editor</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #1e1e2e;
  color: #e0e0e0; display: flex; align-items: center; justify-content: center;
  height: 100vh; margin: 0; }}
.welcome {{ text-align: center; max-width: 500px; }}
h1 {{ color: #7c5cbf; margin-bottom: 16px; }}
p {{ color: #a0a0b0; line-height: 1.6; }}
code {{ background: #313145; padding: 2px 8px; border-radius: 4px; }}
</style></head>
<body><div class="welcome">
<h1>FigRecipe Editor</h1>
<p>{message}</p>
<p>Example: <code>?recipe=examples/01_line.yaml</code></p>
</div></body></html>"""


def _get_recipe_path(request):
    """Extract recipe_path from request query or body."""
    if request.method == "GET":
        return request.GET.get("recipe", "")
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    return data.get("recipe_path", "") or request.GET.get("recipe", "")


def _get_editor(request):
    """Return cached editor for the recipe, or None if no recipe."""
    recipe_path = _get_recipe_path(request)
    if not recipe_path:
        return None
    session_key = f"figrecipe_{recipe_path}"
    try:
        return get_or_create_editor(session_key, recipe_path)
    except FileNotFoundError:
        logger.warning("[FigRecipe] Recipe not found: %s", recipe_path)
        return None


# ── Endpoints that work without an editor ──────────────────────────
_NO_EDITOR_ENDPOINTS = {
    "ping",
    "list_themes",
    "api/tree",
    "api/files",
    "api/switch",
    "api/gallery",
    "api/gallery/add",
    "api/compose",
    "api/chat/stream",
    "api/chat/sessions/",
}


def _favicon_data_uri(hex_color: str) -> str:
    """Build a `data:` URI for a plain rounded-square favicon in `hex_color`.

    No image asset needed — generated inline so per-brand favicons (see
    FIGRECIPE_FAVICON_COLOR below) don't require shipping a new static file
    per consumer package.
    """
    from urllib.parse import quote

    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        f"<rect width='100' height='100' rx='20' fill='{hex_color}'/></svg>"
    )
    return f"data:image/svg+xml,{quote(svg)}"


def editor_page(request):
    """Serve the React SPA inside the scitex-ui workspace shell."""
    import os

    from django.template.loader import render_to_string

    # Try scitex-ui shell template first (standalone with workspace frame)
    try:
        working_dir = os.environ.get("FIGRECIPE_WORKING_DIR", "")
        working_dir_name = Path(working_dir).name if working_dir else "Files"
        # Consumer packages that alias this same CLI/Django app under their
        # own console-script (e.g. scitex-plt) can rebrand the page title
        # and favicon by setting these two env vars before launching the
        # editor (see figrecipe._cli._main's program-name detection) rather
        # than forking the template.
        favicon_color = os.environ.get("FIGRECIPE_FAVICON_COLOR", "")
        html = render_to_string(
            "figrecipe/standalone.html",
            {
                "app_name": "figrecipe",
                "app_label": os.environ.get("FIGRECIPE_APP_LABEL", "FigRecipe Editor"),
                "working_dir": working_dir,
                "working_dir_name": working_dir_name,
                "favicon_href": (
                    _favicon_data_uri(favicon_color) if favicon_color else ""
                ),
            },
            request=request,
        )
        return HttpResponse(html)
    except Exception:
        # Fallback: serve raw React SPA (no shell)
        react_html = _STATIC_DIR / "index.html"
        if react_html.exists():
            return HttpResponse(react_html.read_text())
        return HttpResponse(
            _welcome_page("React build not found. Run: cd frontend && npm run build")
        )


@csrf_exempt
def api_dispatch(request, endpoint):
    """Dispatch API calls to handler functions."""
    editor = _get_editor(request)

    # Some endpoints require an editor
    _no_editor = endpoint in _NO_EDITOR_ENDPOINTS or endpoint.startswith(
        (
            "api/compose/export/",
            "api/gallery/thumbnail/",
            "api/file-content/",
            "api/chat/sessions/",
        )
    )
    if editor is None and not _no_editor:
        handler = HANDLERS.get(endpoint)
        if handler:
            return JsonResponse(
                {"error": "No recipe loaded. Select a file to begin."},
                status=400,
            )

    handler = HANDLERS.get(endpoint)
    if handler:
        try:
            return handler(request, editor)
        except Exception as e:
            logger.exception("[FigRecipe] API error on /%s", endpoint)
            return JsonResponse({"error": str(e)}, status=500)

    # Parameterized endpoints
    if endpoint.startswith("api/gallery/thumbnail/"):
        from .handlers import handle_gallery_thumbnail

        name = endpoint[len("api/gallery/thumbnail/") :]
        try:
            return handle_gallery_thumbnail(request, editor, name)
        except Exception as e:
            logger.exception("[FigRecipe] gallery thumbnail/%s", name)
            return JsonResponse({"error": str(e)}, status=500)

    if endpoint.startswith("call/"):
        if editor is None:
            return JsonResponse({"error": "No recipe loaded"}, status=400)
        call_id = endpoint[5:]
        try:
            return handle_single_call(request, editor, call_id)
        except Exception as e:
            logger.exception("[FigRecipe] API error on /call/%s", call_id)
            return JsonResponse({"error": str(e)}, status=500)

    if endpoint.startswith("download/"):
        if editor is None:
            return JsonResponse({"error": "No recipe loaded"}, status=400)
        fmt = endpoint[9:]
        try:
            return handle_download_fig(request, editor, fmt)
        except Exception as e:
            logger.exception("[FigRecipe] API error on /download/%s", fmt)
            return JsonResponse({"error": str(e)}, status=500)

    if endpoint.startswith("api/compose/export/"):
        from .handlers.compose import handle_compose_export

        fmt = endpoint[len("api/compose/export/") :]
        try:
            return handle_compose_export(request, editor, fmt)
        except Exception as e:
            logger.exception("[FigRecipe] compose export/%s", fmt)
            return JsonResponse({"error": str(e)}, status=500)

    if endpoint.startswith("api/file-content/"):
        from .handlers.files import handle_api_file_content

        file_path = endpoint[len("api/file-content/") :]
        try:
            return handle_api_file_content(request, editor, file_path)
        except Exception as e:
            logger.exception("[FigRecipe] file-content/%s", file_path)
            return JsonResponse({"error": str(e)}, status=500)

    # Chat session parameterized endpoints:
    #   api/chat/sessions/<id>/           -> detail (GET/PATCH/DELETE)
    #   api/chat/sessions/<id>/messages/  -> messages (GET/POST)
    if endpoint.startswith("api/chat/sessions/"):
        from .handlers import handle_api_session_detail, handle_api_session_messages

        rest = endpoint[len("api/chat/sessions/") :]
        # e.g. rest = "42/messages/" or "42/"
        parts = rest.strip("/").split("/")
        try:
            session_id = int(parts[0])
        except (ValueError, IndexError):
            return JsonResponse({"error": "Invalid session ID"}, status=400)

        try:
            if len(parts) >= 2 and parts[1] == "messages":
                return handle_api_session_messages(request, editor, session_id)
            return handle_api_session_detail(request, editor, session_id)
        except Exception as e:
            logger.exception("[FigRecipe] session/%s", rest)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": f"Unknown endpoint: {endpoint}"}, status=404)
