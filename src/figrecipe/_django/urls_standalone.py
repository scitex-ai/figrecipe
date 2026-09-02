#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Root URLconf for the STANDALONE editor server (``figrecipe._django.settings``).

Standalone, Django's development server serves ``/static/`` only while ``DEBUG``
is on, and ``DEBUG`` now defaults OFF (a network-facing 400 was arriving as a
70 KB traceback page; measured 2026-09-02). Without a route of our own, turning
DEBUG off turns the editor into a blank page with two 404s -- the second-order
effect that makes the default flip more than one line.

This lives here and deliberately NOT in ``urls.py``: ``urls.py`` is what a host
application ``include()``s under its own prefix (``_django/__init__.py``), and
a host serves its own static files. A static route there would be dead weight
at best and a shadow at worst.

``insecure=True`` is Django's name for "serve from the finders even though
DEBUG is off" -- the documented switch for exactly this case, a development
server that owns its own assets. It widens nothing: the files are the ones
``STATICFILES_DIRS`` already declares.
"""

from django.contrib.staticfiles.views import serve
from django.urls import path

from .urls import urlpatterns as _app_urlpatterns

urlpatterns = [
    # Must precede the app patterns: ``urls.py`` ends in a ``<path:endpoint>``
    # catch-all that would otherwise swallow ``static/...`` into api_dispatch.
    path("static/<path:path>", serve, {"insecure": True}, name="static"),
    # Spliced, not ``include()``d, so route names stay un-namespaced exactly as
    # they were when ``urls.py`` was the root URLconf.
    *_app_urlpatterns,
]

# EOF
