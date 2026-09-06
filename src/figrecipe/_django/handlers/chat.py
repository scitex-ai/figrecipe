#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chat endpoints: scitex-app's chat views, wired for the figrecipe editor.

These wrappers exist because the editor's dispatch passes an ``editor`` the
chat views do not take. The SESSION views additionally query the ORM, and the
standalone editor runs with no database -- see ``_database_is_configured``.
"""

# Chat: single source of truth from scitex-app (no figrecipe-specific fallback).
# `scitex_app.chat` is a lazily-exposed package attribute (PEP 562
# `__getattr__`), not a real importable submodule -- `from scitex_app.chat
# import X` raises ModuleNotFoundError since that form requires the import
# system to resolve `scitex_app.chat` as an actual submodule. `from
# scitex_app import chat` works: it falls back to attribute lookup on the
# already-imported `scitex_app` package.
from scitex_app import chat as _chat

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
    """Wrapper: chat handler ignores editor.

    DELIBERATELY NOT GATED. Streaming a reply needs no database: measured on
    develop d90cea4 with no DATABASES configured, POST here returns 200 and
    streams, and fails only on a missing API key. Only the three SESSION
    handlers below query the ORM. Gating this one as well would have turned a
    working endpoint into a 501 -- predicted by scitex-app from the import
    chain (_django.py -> ._sse, ._stream: zero ORM references) and confirmed by
    running it.
    """
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
