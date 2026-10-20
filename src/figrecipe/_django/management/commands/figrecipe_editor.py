#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Management command to run the figrecipe editor standalone.

Usage:
    python -m django figrecipe_editor [recipe.yaml] --port 8050
"""

import os
import webbrowser

from ...._utils._optional import missing_extra

try:
    from django.core.management.base import BaseCommand
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


class Command(BaseCommand):
    help = "Run the figrecipe editor as a standalone Django server"

    def add_arguments(self, parser):
        parser.add_argument(
            "recipe",
            nargs="?",
            default="",
            help="Path to recipe YAML file",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8050,
            help="Server port (default: 8050)",
        )
        parser.add_argument(
            "--no-browser",
            action="store_true",
            help="Don't open browser automatically",
        )

    def handle(self, *args, **options):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")

        recipe = options["recipe"]
        port = options["port"]
        url = f"http://127.0.0.1:{port}/"
        if recipe:
            url += f"?recipe={recipe}"

        if not options["no_browser"]:
            import threading

            threading.Timer(1.0, webbrowser.open, args=[url]).start()

        self.stdout.write(f"FigRecipe Editor running at {url}")
        self.stdout.write("Press Ctrl+C to stop")

        try:
            from django.core.management import call_command
        except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
            raise missing_extra(exc) from exc

        call_command("runserver", f"127.0.0.1:{port}", "--noreload")
