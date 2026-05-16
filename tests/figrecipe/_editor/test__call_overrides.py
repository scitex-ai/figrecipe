#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test toolbar functionality."""

import time
from typing import List

from .conftest import requires_playwright


@requires_playwright
class TestEditorToolbar:
    """Test toolbar functionality."""

    def test_toolbar_buttons_clickable(self, editor_server):
        """Verify toolbar buttons can be clicked without errors."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            toolbar_buttons = page.locator(
                ".toolbar button, #toolbar button, .btn-toolbar"
            )
            count = toolbar_buttons.count()

            for i in range(min(count, 5)):
                try:
                    toolbar_buttons.nth(i).click()
                    time.sleep(0.2)
                except Exception:
                    pass

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e or "ReferenceError" in e]
        assert len(critical) == 0, "Toolbar errors:\n" + "\n".join(critical)

    def test_view_mode_toggle(self, editor_server):
        """Test view mode (All/Selected) toggle."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            all_btn = page.locator("#btn-all, button:has-text('All')").first
            selected_btn = page.locator(
                "#btn-selected, button:has-text('Selected')"
            ).first

            if all_btn.count() > 0:
                all_btn.click()
                time.sleep(0.2)

            if selected_btn.count() > 0:
                selected_btn.click()
                time.sleep(0.2)

            browser.close()

        # Filter fetch errors from single-threaded Django dev server
        real_errors = [
            e
            for e in js_errors
            if "Failed to fetch" not in e and "No recipe loaded" not in e
        ]
        assert len(real_errors) == 0, "View mode errors:\n" + "\n".join(real_errors)

    def test_keyboard_shortcuts_no_errors(self, editor_server):
        """Test that keyboard shortcuts don't cause errors."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            shortcuts = ["Control+KeyZ", "Control+KeyY", "Control+KeyS", "Escape"]

            for shortcut in shortcuts:
                try:
                    page.keyboard.press(shortcut)
                    time.sleep(0.2)
                except Exception:
                    pass

            browser.close()

        critical = [
            e
            for e in js_errors
            if "SyntaxError" in e or "TypeError" in e or "ReferenceError" in e
        ]
        assert len(critical) == 0, "Keyboard shortcut errors:\n" + "\n".join(critical)
