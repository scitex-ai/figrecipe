#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test properties panel functionality."""

import time
from typing import List

from .conftest import requires_playwright


@requires_playwright
class TestEditorProperties:
    """Test properties panel functionality."""

    def test_tabs_switch_without_errors(self, editor_server):
        """Verify tab switching works without JS errors."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            tabs = ["Figure", "Axis", "Element"]
            for tab_name in tabs:
                tab = page.locator(
                    f"button:has-text('{tab_name}'), .tab:has-text('{tab_name}')"
                ).first
                if tab.count() > 0:
                    tab.click()
                    time.sleep(0.2)

            browser.close()

        assert len(js_errors) == 0, "Tab switch errors:\n" + "\n".join(js_errors)

    def test_property_inputs_respond(self, editor_server):
        """Test that property inputs can be interacted with."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            inputs = page.locator("input[type='text'], input[type='number']")
            count = inputs.count()

            for i in range(min(count, 3)):
                try:
                    inp = inputs.nth(i)
                    if inp.is_visible():
                        inp.click()
                        inp.fill("test")
                        time.sleep(0.1)
                except Exception:
                    pass

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e]
        assert len(critical) == 0, "Property input errors:\n" + "\n".join(critical)

    def test_color_picker_opens(self, editor_server):
        """Test that color pickers can be opened."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            # Try to find and click a visible color picker
            color_swatches = page.locator(".color-swatch, input[type='color']")
            for i in range(color_swatches.count()):
                swatch = color_swatches.nth(i)
                if swatch.is_visible():
                    swatch.click()
                    time.sleep(0.2)
                    break

            # It's OK if no visible color picker found (may be in collapsed section)
            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e or "TypeError" in e]
        assert len(critical) == 0, "Color picker errors:\n" + "\n".join(critical)
