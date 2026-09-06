#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handler package -- thin Django wrappers around figrecipe Python API.

Exports HANDLERS dict for the catch-all dispatcher.
"""

# Chat: single source of truth from scitex-app (no figrecipe-specific fallback).
# `scitex_app.chat` is a lazily-exposed package attribute (PEP 562
# `__getattr__`), not a real importable submodule -- `from scitex_app.chat
# import X` raises ModuleNotFoundError since that form requires the import
# system to resolve `scitex_app.chat` as an actual submodule. `from
# scitex_app import chat` works: it falls back to attribute lookup on the
# already-imported `scitex_app` package.
from scitex_app import chat as _chat

from .annotation import (
    handle_get_captions,
    handle_update_annotation_position,
    handle_update_caption,
)
from .axis import (
    handle_get_axes_positions,
    handle_get_axis_info,
    handle_get_labels,
    handle_get_legend_info,
    handle_update_axes_position,
    handle_update_axis_type,
    handle_update_label,
    handle_update_legend_position,
)
from .compose import handle_compose_save
from .core import handle_hitmap, handle_ping, handle_preview, handle_update
from .datatable import (
    handle_datatable_data,
    handle_datatable_import,
    handle_datatable_plot,
)
from .downloads import handle_download_csv, handle_download_fig
from .elements import (
    handle_calls,
    handle_single_call,
    handle_update_call,
    handle_update_element_color,
)
from .files import (
    handle_api_delete,
    handle_api_download_recipe,
    handle_api_duplicate,
    handle_api_files,
    handle_api_new,
    handle_api_rename,
    handle_api_switch,
    handle_api_tree,
)
from .gallery import (
    handle_gallery_add,
    handle_gallery_available,
    handle_gallery_demo,
    handle_gallery_thumbnail,
)
from .image import (
    handle_add_image_from_url,
    handle_add_image_panel,
    handle_load_recipe,
)
from .stats import (
    handle_stats_add_bracket,
    handle_stats_list_brackets,
    handle_stats_remove_bracket,
    handle_stats_update_bracket,
)
from .style import (
    handle_diff,
    handle_get_theme,
    handle_list_themes,
    handle_overrides,
    handle_restore,
    handle_save,
    handle_style,
    handle_switch_theme,
)

_raw_chat_stream = _chat.chat_stream_view
_raw_session_detail = _chat.session_detail_view
_raw_session_list = _chat.session_list_view
_raw_session_messages = _chat.session_messages_view


def _database_is_configured() -> bool:
    """Is there a database these chat views can actually query?

    The standalone editor runs with no DATABASES entry -- Django's dummy
    backend -- because figrecipe itself stores nothing. The chat views are
    scitex_app's and DO issue ORM queries, so on that configuration every one
    of them raised ImproperlyConfigured and the endpoint answered 500 with a
    Django settings diagnostic in the response body (measured 2026-09-06 on
    develop d90cea4, reported by scitex-app). A host that embeds these
    handlers -- scitex-hub, scitex-cloud -- configures a real database, and
    there the same endpoints must keep working; hence a check, not a deletion.
    """
    from django.conf import settings

    default = (getattr(settings, "DATABASES", None) or {}).get("default") or {}
    engine = default.get("ENGINE") or ""
    return bool(engine) and not engine.endswith("dummy")


def _chat_unavailable(request):
    """Say the feature is not available here, in the feature's own terms.

    NOT a 500, and not a Django internals string: the caller asked for chat
    history from a build that has no store to keep it in, which is a fact
    about this deployment rather than a fault. 501 is the honest code -- the
    endpoint exists in the API and this server does not implement it.
    """
    from django.http import JsonResponse

    return JsonResponse(
        {
            "error": "chat history is not available in the standalone editor",
            "detail": (
                "The standalone editor runs without a database, so chat "
                "sessions are not stored. This feature is available in the "
                "hosted editor."
            ),
        },
        status=501,
    )


def handle_api_chat_stream(request, editor):
    """Wrapper: chat handler ignores editor."""
    if not _database_is_configured():
        return _chat_unavailable(request)
    return _raw_chat_stream(request)


def handle_api_session_list(request, editor):
    """Wrapper: session list/create — ignores editor."""
    if not _database_is_configured():
        return _chat_unavailable(request)
    return _raw_session_list(request)


def handle_api_session_detail(request, editor, session_id):
    """Wrapper: session get/patch/delete — ignores editor."""
    if not _database_is_configured():
        return _chat_unavailable(request)
    return _raw_session_detail(request, session_id)


def handle_api_session_messages(request, editor, session_id):
    """Wrapper: session messages get/add — ignores editor."""
    if not _database_is_configured():
        return _chat_unavailable(request)
    return _raw_session_messages(request, session_id)


# fmt: off
HANDLERS = {
    # Core
    "preview":                      handle_preview,
    "ping":                         handle_ping,
    "update":                       handle_update,
    "hitmap":                       handle_hitmap,

    # Style
    "style":                        handle_style,
    "overrides":                    handle_overrides,
    "theme":                        handle_get_theme,
    "list_themes":                  handle_list_themes,
    "switch_theme":                 handle_switch_theme,
    "save":                         handle_save,
    "restore":                      handle_restore,
    "diff":                         handle_diff,

    # Axis
    "get_labels":                   handle_get_labels,
    "update_label":                 handle_update_label,
    "update_axis_type":             handle_update_axis_type,
    "get_axis_info":                handle_get_axis_info,
    "get_legend_info":              handle_get_legend_info,
    "update_legend_position":       handle_update_legend_position,
    "get_axes_positions":           handle_get_axes_positions,
    "update_axes_position":         handle_update_axes_position,

    # Elements
    "calls":                        handle_calls,
    "update_call":                  handle_update_call,
    "update_element_color":         handle_update_element_color,

    # Annotation
    "update_annotation_position":   handle_update_annotation_position,
    "get_captions":                 handle_get_captions,
    "update_caption":               handle_update_caption,

    # Datatable
    "datatable/data":               handle_datatable_data,
    "datatable/plot":               handle_datatable_plot,
    "datatable/import":             handle_datatable_import,

    # Downloads
    "download/csv":                 handle_download_csv,

    # Image drops
    "add_image_panel":              handle_add_image_panel,
    "add_image_from_url":           handle_add_image_from_url,
    "load_recipe":                  handle_load_recipe,

    # Files
    "api/tree":                     handle_api_tree,
    "api/files":                    handle_api_files,
    "api/switch":                   handle_api_switch,
    "api/new":                      handle_api_new,
    "api/delete":                   handle_api_delete,
    "api/rename":                   handle_api_rename,
    "api/duplicate":                handle_api_duplicate,
    "api/download":                 handle_api_download_recipe,

    # Gallery
    "api/gallery":                  handle_gallery_available,
    "api/gallery/add":              handle_gallery_add,
    "api/gallery/demo":             handle_gallery_demo,

    # Compose
    "api/compose":                  handle_compose_save,

    # Chat
    "api/chat/stream":              handle_api_chat_stream,
    "api/chat/sessions/":           handle_api_session_list,

    # Stats annotations
    "stats/add_bracket":            handle_stats_add_bracket,
    "stats/remove_bracket":         handle_stats_remove_bracket,
    "stats/update_bracket":         handle_stats_update_bracket,
    "stats/list_brackets":          handle_stats_list_brackets,
}
# fmt: on

__all__ = [
    "HANDLERS",
    "handle_single_call",
    "handle_download_fig",
    "handle_gallery_demo",
    "handle_gallery_thumbnail",
    "handle_compose_export",
]
