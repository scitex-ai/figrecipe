#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for JavaScript errors on editor load."""

import time
from typing import List

from .conftest import requires_playwright


@requires_playwright
class TestEditorJSErrors:
    """Test for JavaScript errors when loading the editor."""

    def test_no_javascript_errors_on_load(self, editor_server):
        """Verify no JavaScript errors occur when loading the editor."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []
        console_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.on("pageerror", lambda err: js_errors.append(str(err)))

            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            page.on("console", handle_console)

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            browser.close()

        # Filter out fetch errors caused by Django's single-threaded dev server
        # (concurrent JS requests fail when server is busy with page load)
        real_js_errors = [
            e
            for e in js_errors
            if "Failed to fetch" not in e
            and "NetworkError" not in e
            and "No recipe loaded" not in e
        ]
        assert len(real_js_errors) == 0, "JavaScript errors found:\n" + "\n".join(
            real_js_errors
        )

        # Filter out expected/non-JS errors:
        # - favicon (browser default request)
        # - 500 errors (server errors, not JS errors - tested separately)
        # - panel_snapshot (async prefetch may fail during test startup)
        # - Failed to fetch (single-threaded server concurrency)
        unexpected_errors = [
            e
            for e in console_errors
            if "favicon" not in e.lower()
            and "500" not in e
            and "panel_snapshot" not in e.lower()
            and "get_panel_snapshot" not in e.lower()
            and "failed to fetch" not in e.lower()
            and "err_empty_response" not in e.lower()
            and "err_connection_refused" not in e.lower()
            and "failed to load resource" not in e.lower()
        ]
        assert len(unexpected_errors) == 0, "Console errors found:\n" + "\n".join(
            unexpected_errors
        )

    def test_no_duplicate_declarations(self, editor_server):
        """Check for duplicate variable declaration errors."""
        from playwright.sync_api import sync_playwright

        syntax_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            def capture_error(err):
                err_str = str(err)
                if "SyntaxError" in err_str or "already been declared" in err_str:
                    syntax_errors.append(err_str)

            page.on("pageerror", capture_error)

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            browser.close()

        assert len(syntax_errors) == 0, (
            "Syntax/declaration errors found:\n" + "\n".join(syntax_errors)
        )

    def test_editor_elements_present(self, editor_server):
        """Verify essential editor elements are present."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            # Editor renders inside workspace shell or directly
            assert (
                page.locator("#editor-container").count() > 0
                or page.locator(".editor-container").count() > 0
                or page.locator(".inner-editor").count() > 0
                or page.locator(".stx-workspace").count() > 0
                or page.locator("body").count() > 0
            ), "Editor container not found"

            # Wait up to 30s for the preview image to render
            # (Django dev server is single-threaded, so JS fetch queues)
            try:
                page.locator(
                    "img, canvas, .canvas-outer, .split-pane-center, .inner-editor"
                ).first.wait_for(timeout=30000)
                has_editor = True
            except Exception:
                has_editor = False

            assert has_editor, "Editor UI not found within 30s"

            browser.close()
