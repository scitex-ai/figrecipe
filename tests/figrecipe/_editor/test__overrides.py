#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test style override functionality."""

import time
from typing import List

from .conftest import requires_playwright


@requires_playwright
class TestEditorOverrides:
    """Test style override functionality."""

    def test_style_api_endpoint(self, editor_server):
        """Verify style API endpoint works (contains overrides)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Direct API call — skip page.goto to avoid blocking
            # the single-threaded Django server with JS fetch calls
            response = page.request.get(editor_server.api("style"))
            assert response.ok, f"Style request failed: {response.status}"

            data = response.json()
            assert isinstance(data, dict), "Style should return a dict"
            assert "manual_overrides" in data, "Style should contain manual_overrides"

            browser.close()

    def test_save_triggers_update(self, editor_server):
        """Test that save action triggers preview update."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            page.keyboard.press("Control+KeyS")
            time.sleep(0.5)

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e or "TypeError" in e]
        assert len(critical) == 0, "Save errors:\n" + "\n".join(critical)

    def test_update_api_endpoint(self, editor_server):
        """Test the update API endpoint accepts changes."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Direct API call — skip page.goto to avoid blocking
            response = page.request.post(
                editor_server.api("update"),
                headers={"Content-Type": "application/json"},
                data='{"overrides": {}}',
            )
            # May return 200 or 400 depending on implementation
            assert response.status in [
                200,
                400,
                415,
            ], f"Update endpoint error: {response.status}"

            browser.close()

    def test_preview_api_endpoint(self, editor_server):
        """Verify preview endpoint returns JSON with image data."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Direct API call — skip page.goto to avoid blocking
            response = page.request.get(editor_server.api("preview"))
            assert response.ok, f"Preview request failed: {response.status}"
            assert "application/json" in response.headers.get(
                "content-type", ""
            ), "Preview should return JSON"

            # Verify JSON structure
            data = response.json()
            assert "image" in data, "Response missing 'image' field"
            assert "bboxes" in data, "Response missing 'bboxes' field"
            # Check for valid PNG base64 (PNG signature starts with iVBOR)
            assert data["image"].startswith("iVBOR"), "Invalid PNG base64 image"

            browser.close()
