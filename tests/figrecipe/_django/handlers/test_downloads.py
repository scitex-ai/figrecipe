#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the figure-download handler and the Plot-tab export surface.

Mirrors ``src/figrecipe/_django/handlers/downloads.py`` (PS-204 mirror rule).

Standalone item #4 — "nothing on screen saves an image" — is closed on the
Plot tab by adding an Export button to FigureViewer that opens the existing
ExportDialog. The backend it calls already shipped (``download/<fmt>`` →
``handle_download_fig``, PNG/SVG/PDF at 300 DPI), so these guards pin both
halves:

  1. Backend — ``handle_download_fig`` renders a real image for png and svg
     (driven with a reproduced figure, the same path the editor uses to load a
     recipe) and rejects an unknown format.
  2. Frontend contract — FigureViewer.tsx exposes the export control, gated on
     a loaded figure, and opens the ExportDialog. (The repo has no React/DOM
     runner; the frontend is gated by the vite build, so the wiring is pinned
     by source contract, matching test_files_api_switch_reload.py.)

Each test makes a single assertion (STX-TQ007): the checks are collected in
Arrange/Act and folded into one Assert.
"""

import os

import pytest

django = pytest.importorskip("django")


@pytest.fixture(scope="module")
def _django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


def _package_root():
    from pathlib import Path

    import figrecipe

    return Path(figrecipe.__file__).resolve().parent


def _editor_with_recipe():
    from figrecipe._django.services import get_or_create_editor

    # get_or_create_editor reproduces the recipe into an EditorState (the same
    # path the editor uses when a recipe is opened), so handle_download_fig
    # receives a real editor.fig to render.
    recipe = _package_root() / "_django" / "gallery_templates" / "plot_plot.yaml"
    return get_or_create_editor(f"dl4_{recipe}", str(recipe))


class TestDownloadFig:
    def test_download_png_renders_a_real_image(self, _django_ready):
        # Arrange
        from django.test import RequestFactory

        from figrecipe._django.handlers.downloads import handle_download_fig

        editor = _editor_with_recipe()
        # Act
        resp = handle_download_fig(RequestFactory().get("download/png"), editor, "png")
        problems = []
        if resp.status_code != 200:
            problems.append(f"status={resp.status_code}")
        if resp["Content-Type"] != "image/png":
            problems.append(f"content-type={resp['Content-Type']}")
        body = resp.content
        if not (len(body) > 1000 and body[:8] == b"\x89PNG\r\n\x1a\n"):
            problems.append(f"body not a real PNG ({len(body)} bytes)")
        # Assert
        assert problems == [], "png download failed: " + "; ".join(problems)

    def test_download_svg_renders_svg_document(self, _django_ready):
        # Arrange
        from django.test import RequestFactory

        from figrecipe._django.handlers.downloads import handle_download_fig

        editor = _editor_with_recipe()
        # Act
        resp = handle_download_fig(RequestFactory().get("download/svg"), editor, "svg")
        problems = []
        if resp.status_code != 200:
            problems.append(f"status={resp.status_code}")
        if resp["Content-Type"] != "image/svg+xml":
            problems.append(f"content-type={resp['Content-Type']}")
        if b"<svg" not in resp.content[:200]:
            problems.append("body does not start with <svg")
        # Assert
        assert problems == [], "svg download failed: " + "; ".join(problems)

    def test_download_rejects_an_unknown_format(self, _django_ready):
        # Arrange
        from django.test import RequestFactory

        from figrecipe._django.handlers.downloads import handle_download_fig

        editor = _editor_with_recipe()
        # Act
        resp = handle_download_fig(
            RequestFactory().get("download/bmp"), editor, "bmp"
        )
        # Assert
        assert resp.status_code == 400, f"bmp download should 400, got {resp.status_code}"


class TestPlotTabExportSurface:
    def test_figure_viewer_exposes_the_export_control(self, _django_ready):
        # Arrange -- read the component source by path (importing the frontend
        # is a build concern, not a Python one).
        src = (
            _package_root()
            / "_django"
            / "frontend"
            / "src"
            / "components"
            / "FigureViewer"
            / "FigureViewer.tsx"
        ).read_text(encoding="utf-8")
        # Act
        contract = {
            "export button": "figure-viewer__export" in src,
            "opens the dialog": "ExportDialog" in src and "setExportOpen(true)" in src,
            "gated on a loaded figure": "previewImage && (" in src,
        }
        # Assert
        assert all(contract.values()), (
            "FigureViewer export surface incomplete: "
            + "; ".join(k for k, ok in contract.items() if not ok)
        )
