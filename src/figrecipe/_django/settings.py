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

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

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

ROOT_URLCONF = "figrecipe._django.urls"

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

# No DATABASES entry: this app declares no models and issues no ORM queries,
# so there is nothing to store. Django treats an unset DATABASES as the dummy
# backend and skips the unapplied-migration check, which is exactly what the
# standalone editor wants. The peer launcher (scitex_app._standalone) already
# configures Django the same way.

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATICFILES_DIRS = [str(BASE_DIR / "static")]

# Temp directory for session files
FIGRECIPE_TEMP_DIR = Path(tempfile.gettempdir()) / "figrecipe_editor"
