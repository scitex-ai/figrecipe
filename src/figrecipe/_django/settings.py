#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal Django settings for standalone figrecipe editor.

Used when running the editor without a parent Django project.
"""

import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "figrecipe-standalone-dev-key-not-for-production",
)

# Off unless asked for. With DEBUG on, a request from any non-loopback host
# was answered with Django's technical 400 page -- 70,205 bytes of traceback and
# settings -- to whoever sent it (measured 2026-09-02 against 0.34.6). A
# standalone server is the one figrecipe surface that faces a network, so the
# default must be the safe one; ``DJANGO_DEBUG=true`` opts back in for
# development. The GUI's own assets keep being served with DEBUG off -- see
# ``urls_standalone.py`` for why that needs its own route.
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

# Loopback, plus whatever the launcher says the bind implies. ``gui()`` writes
# SCITEX_ALLOWED_HOSTS from ``_allowed_hosts.apply_bound_host`` BEFORE
# django.setup(): binding to an address is the statement that you intend to be
# reached on it, and "0.0.0.0" in this list never matches a real interface
# address in a Host header (measured 2026-09-02: `--host 0.0.0.0` answered 400
# to every non-loopback caller). Read once here, at import -- hence the order.
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"] + [
    _h.strip()
    for _h in os.environ.get("SCITEX_ALLOWED_HOSTS", "").split(",")
    if _h.strip() and _h.strip() not in ("127.0.0.1", "localhost", "0.0.0.0")
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "figrecipe._django",
    "figrecipe._django.apps.ScitexAppChatConfig",
]

# Optional: scitex-ui shared components (static assets served via AppDirectoriesFinder)
try:
    import scitex_ui  # noqa: F401

    INSTALLED_APPS.append("scitex_ui")
except ImportError:
    pass

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# The STANDALONE root URLconf, not ``urls.py``: ``urls.py`` is the module a host
# application ``include()``s under its own prefix (``_django/__init__.py``), and
# the static route standalone needs must not ride along into a host.
ROOT_URLCONF = "figrecipe._django.urls_standalone"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# No DATABASES entry: Django then uses the dummy backend, which raises on any
# query, and skips the unapplied-migration check -- which is what the standalone
# editor wants, because figrecipe stores nothing of its own.
#
# BUT NOTE WHAT ELSE IS INSTALLED. INSTALLED_APPS above registers
# ScitexAppChatConfig (scitex_app._chat), whose ChatSession/ChatMessage views
# DO issue ORM queries, and the handler registry routes api/chat/* to them. On
# 2026-09-06 that combination answered 500 on every call to
# /api/chat/sessions/, with the Django settings diagnostic in the response
# body. This comment previously read "this app declares no models and issues no
# ORM queries, so there is nothing to store" -- true of figrecipe's own app,
# false of this settings module, and standing right next to the wiring that
# contradicted it.
#
# The handlers now check for a usable database and answer 501 here instead
# (see _django/handlers/__init__.py::_database_is_configured). The app stays
# registered so the models remain importable on the shared handler path; a host
# that embeds these handlers with a real database keeps the working feature.

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATICFILES_DIRS = [str(BASE_DIR / "static")]

# Temp directory for session files
FIGRECIPE_TEMP_DIR = Path(tempfile.gettempdir()) / "figrecipe_editor"
