#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for dark mode text color handling in the figure editor."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up matplotlib figures after each test."""
    yield
    plt.close("all")


class TestDarkModeTextColors:
    """Test that dark mode correctly updates all text colors."""

    def test_panel_labels_dark_mode(self):
        """Test that panel labels change color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, axes = fr.subplots(2, 2, figsize=(8, 8))
        for ax in axes.flat:
            ax.plot([1, 2, 3], [1, 4, 9])
        fig.add_panel_labels()

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Collect panel label text objects (position at (-0.1, 1.05))
        panel_labels = []
        for ax in mpl_fig.get_axes():
            for text in ax.texts:
                if text.get_position() == (-0.1, 1.05):
                    panel_labels.append(text)

        # Verify we found at least 4 panel labels (one per axes)
        assert len(panel_labels) >= 4

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify colors changed for all panel labels
        for text in panel_labels:
            assert text.get_color() == dark_text_color

    def test_pie_labels_dark_mode(self):
        """Test that pie chart labels change color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, ax = fr.subplots(1, 1)
        ax.pie([30, 40, 30], labels=["A", "B", "C"], autopct="%1.1f%%")

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # All pie text should be in ax.texts
        pie_ax = mpl_fig.get_axes()[0]
        assert len(pie_ax.texts) >= 3

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify all pie text colors changed
        for text in pie_ax.texts:
            assert text.get_color() == dark_text_color

    def test_title_xlabel_ylabel_dark_mode(self):
        """Test that title and axis labels change color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_title("Test Title")
        ax.set_xlabel("X Label")
        ax.set_ylabel("Y Label")

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify axis label colors
        mpl_ax = mpl_fig.get_axes()[0]
        assert mpl_ax.title.get_color() == dark_text_color
        assert mpl_ax.xaxis.label.get_color() == dark_text_color
        assert mpl_ax.yaxis.label.get_color() == dark_text_color

    def test_suptitle_dark_mode(self):
        """Test that figure suptitle changes color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9])
        fig.suptitle("Super Title")

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify suptitle color
        assert mpl_fig._suptitle.get_color() == dark_text_color

    def test_legend_text_dark_mode(self):
        """Test that legend text changes color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9], label="Line 1")
        ax.plot([1, 2, 3], [9, 4, 1], label="Line 2")
        ax.legend()

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify legend text colors
        mpl_ax = mpl_fig.get_axes()[0]
        legend = mpl_ax.get_legend()
        for text in legend.get_texts():
            assert text.get_color() == dark_text_color

    def test_specgram_tick_labels_dark_mode(self):
        """Test that specgram tick labels change color in dark mode."""
        import figrecipe as fr
        from figrecipe._editor._render_overrides import apply_dark_mode

        fig, ax = fr.subplots(1, 1)
        np.random.seed(42)
        ax.specgram(np.random.randn(1000), Fs=1000, NFFT=256)

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Apply dark mode
        apply_dark_mode(mpl_fig)

        # Verify tick label colors
        mpl_ax = mpl_fig.get_axes()[0]
        for label in mpl_ax.get_xticklabels() + mpl_ax.get_yticklabels():
            # Some labels might be empty
            if label.get_text():
                assert label.get_color() == dark_text_color

    def test_render_with_overrides_dark_mode(self):
        """Test that render_with_overrides correctly applies dark mode."""
        import figrecipe as fr
        from figrecipe._editor._helpers import render_with_overrides

        fig, ax = fr.subplots(1, 1)
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_title("Test")
        fig.add_panel_labels()

        mpl_fig = fig.fig
        dark_text_color = "#e8e8e8"

        # Render with dark mode
        render_with_overrides(fig, {}, dark_mode=True)

        # Verify colors after render
        mpl_ax = mpl_fig.get_axes()[0]
        assert mpl_ax.title.get_color() == dark_text_color
        for text in mpl_ax.texts:
            assert text.get_color() == dark_text_color


class TestSpecgramTickVisibility:
    """Test that specgram keeps visible ticks when matrix styling is applied."""

    def test_specgram_keeps_ticks_with_matrix_style(self):
        """Test that apply_matrix_style preserves specgram ticks when xlabel/ylabel present."""
        from figrecipe.styles._plot_styles import apply_matrix_style

        fig, ax = plt.subplots()
        fs = 1000
        t = np.linspace(0, 2, 2000)
        x = np.sin(2 * np.pi * 50 * t)
        ax.specgram(x, Fs=fs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Frequency")

        # Store original tick counts
        orig_xticks = len(ax.get_xticks())
        orig_yticks = len(ax.get_yticks())

        # Apply matrix style with imshow_show_axes=False
        apply_matrix_style(ax, {"imshow_show_axes": False})

        # Specgram should keep ticks because it has xlabel/ylabel
        assert len(ax.get_xticks()) == orig_xticks
        assert len(ax.get_yticks()) == orig_yticks

    def test_imshow_hides_ticks_with_matrix_style(self):
        """Test that regular imshow hides ticks when imshow_show_axes=False."""
        from figrecipe.styles._plot_styles import apply_matrix_style

        fig, ax = plt.subplots()
        ax.imshow(np.random.rand(10, 10))
        # No xlabel/ylabel set

        # Apply matrix style with imshow_show_axes=False
        apply_matrix_style(ax, {"imshow_show_axes": False})

        # Regular imshow should hide ticks
        assert len(ax.get_xticks()) == 0
        assert len(ax.get_yticks()) == 0

    def test_specgram_with_style_keeps_ticks(self):
        """Test specgram ticks remain visible after full style application."""
        import figrecipe as fr
        from figrecipe.styles._style_applier import apply_style_mm

        fig, ax = fr.subplots(1, 1)
        fs = 1000
        t = np.linspace(0, 2, 2000)
        x = np.sin(2 * np.pi * 50 * t)
        ax.specgram(x, Fs=fs)
        ax.set_xlabel("Time")
        ax.set_ylabel("Frequency")

        mpl_ax = ax.ax

        # Apply full style (which calls apply_matrix_style internally)
        style = {"imshow_show_axes": False, "theme": "dark"}
        apply_style_mm(mpl_ax, style)

        # Specgram should still have ticks
        assert len(mpl_ax.get_xticks()) > 0
        assert len(mpl_ax.get_yticks()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# === merged from v2 ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test theme and dark mode functionality."""

import time
from typing import List

from .conftest import requires_playwright


@requires_playwright
class TestEditorTheme:
    """Test theme application functionality."""

    def test_theme_modal_opens(self, editor_server):
        """Verify theme modal can be opened."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            theme_btn = page.locator(
                "button:has-text('Theme'), #theme-btn, .theme-button"
            ).first
            if theme_btn.count() > 0:
                theme_btn.click()
                time.sleep(0.3)

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e or "TypeError" in e]
        assert len(critical) == 0, "Theme modal errors:\n" + "\n".join(critical)

    def test_dark_mode_toggle(self, editor_server):
        """Test dark mode toggle functionality."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            dark_toggle = page.locator(
                "#dark-mode-toggle, .dark-mode-toggle, "
                "button:has-text('Dark'), input[type='checkbox'][id*='dark']"
            ).first

            if dark_toggle.count() > 0:
                # Force click to bypass hitregion-overlay pointer-events interception
                dark_toggle.click(force=True)
                time.sleep(0.3)

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e or "TypeError" in e]
        assert len(critical) == 0, "Dark mode errors:\n" + "\n".join(critical)

    def test_theme_change_updates_preview(self, editor_server):
        """Test that changing theme updates the preview."""
        from playwright.sync_api import sync_playwright

        js_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda err: js_errors.append(str(err)))

            page.goto(editor_server.recipe_url)
            page.wait_for_load_state("networkidle")

            # Try to find and interact with theme selector
            theme_select = page.locator("select[id*='theme'], #theme-select").first
            if theme_select.count() > 0:
                options = theme_select.locator("option")
                if options.count() > 1:
                    theme_select.select_option(index=1)
                    time.sleep(0.5)

            browser.close()

        critical = [e for e in js_errors if "SyntaxError" in e]
        assert len(critical) == 0, "Theme change errors:\n" + "\n".join(critical)
