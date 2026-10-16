#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test toolbar functionality."""

import subprocess
import sys
import time
from pathlib import Path
from typing import List

from .conftest import _REPO_ROOT, _REPO_SRC, requires_playwright


@requires_playwright
class TestEditorToolbar:
    """Test toolbar functionality."""

    def test_toolbar_buttons_clickable(self, editor_server):
        """Verify toolbar buttons can be clicked without errors."""
        # Arrange
        # Act
        # Assert
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
        # Arrange
        # Act
        # Assert
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
        # Arrange
        # Act
        # Assert
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


class TestEditorServerChildImport:
    """The child interpreter launched by EditorServer imports src/figrecipe.

    Regression: the fixture used to launch with cwd=tests and a relative
    'src' sys.path entry, which resolved to the nonexistent tests/src, so
    `import figrecipe` bound to the tests/figrecipe package (no gui) and
    the server died before any browser test ran.
    """

    def _run_child(self, code: str):
        """Run a child Python snippet with the same launch as EditorServer."""
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
            timeout=30,
        )

    def test_child_resolves_figrecipe_to_repo_src(self):
        """Child process resolves figrecipe to the repo's src/ tree."""
        # Arrange — replicate the child launch exactly as EditorServer does.
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(_REPO_SRC)!r})\n"
            "import figrecipe\n"
            "print(figrecipe.__file__)\n"
        )
        # Act
        result = self._run_child(code)
        # Assert
        assert result.returncode == 0, (
            f"child failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_child_resolved_path_is_under_repo_src(self):
        """The resolved figrecipe path is under the repo's src/ directory."""
        # Arrange
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(_REPO_SRC)!r})\n"
            "import figrecipe\n"
            "print(figrecipe.__file__)\n"
        )
        # Act
        result = self._run_child(code)
        resolved = result.stdout.strip()
        # Assert
        assert Path(resolved).is_relative_to(_REPO_SRC), (
            f"child imported figrecipe from {resolved}, "
            f"expected under {_REPO_SRC}"
        )

    def test_child_resolved_path_is_not_tests_package(self):
        """The resolved figrecipe path is not the tests/ package."""
        # Arrange
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(_REPO_SRC)!r})\n"
            "import figrecipe\n"
            "print(figrecipe.__file__)\n"
        )
        # Act
        result = self._run_child(code)
        resolved = result.stdout.strip()
        # Assert
        assert "tests" not in Path(resolved).parts, (
            f"child imported figrecipe from the tests package: {resolved}"
        )

    def test_child_has_gui_attribute(self):
        """Child process can access fr.gui (the entry point the server calls)."""
        # Arrange
        code = (
            "import sys\n"
            f"sys.path.insert(0, {str(_REPO_SRC)!r})\n"
            "import figrecipe as fr\n"
            "assert hasattr(fr, 'gui'), 'fr.gui missing'\n"
            "print('ok')\n"
        )
        # Act
        result = self._run_child(code)
        # Assert
        assert result.returncode == 0, (
            f"child failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_repo_root_anchors_to_repo_root(self):
        """_REPO_ROOT anchors to the repo root (tests/ -> repo root)."""
        # Arrange
        # conftest.py is at tests/figrecipe/_editor/conftest.py
        expected = Path(__file__).resolve().parent.parent.parent.parent
        # Act
        # Assert
        assert _REPO_ROOT == expected

    def test_repo_root_has_src_figrecipe(self):
        """_REPO_ROOT contains src/figrecipe/__init__.py."""
        # Arrange
        # Act
        # Assert
        assert (_REPO_ROOT / "src" / "figrecipe" / "__init__.py").exists()

    def test_repo_root_has_tests_figrecipe(self):
        """_REPO_ROOT contains tests/figrecipe/__init__.py."""
        # Arrange
        # Act
        # Assert
        assert (_REPO_ROOT / "tests" / "figrecipe" / "__init__.py").exists()
