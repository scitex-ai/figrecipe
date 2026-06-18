#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for the editor recipe-switch / new-figure reload flow.

`handle_api_switch` / `handle_api_new` reload a recipe into an existing editor
and must reset its style overrides. They used to call `editor._init_style_overrides(None)`,
a method that no longer exists on EditorState (overrides became a lazy property),
so selecting any recipe in the GUI 500'd on `/api/switch` and the canvas stayed
blank. The reset is now `editor._overrides = None` (lazy rebuild from style).
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr
from figrecipe._django.services import get_or_create_editor


class TestEditorReloadFlow:
    def test_reload_renders_after_overrides_reset(self):
        # Arrange -- a saved recipe + an editor (the GUI's per-file state).
        from figrecipe._editor._helpers import render_with_overrides

        with tempfile.TemporaryDirectory() as tmpdir:
            recipe = Path(tmpdir) / "fig.yaml"
            fig, ax = fr.subplots()
            ax.plot([1, 2, 3], [4, 5, 6])
            fr.save(fig, recipe, validate=False, verbose=False)
            editor = get_or_create_editor(f"k_{recipe}", str(recipe))
            # Act -- the exact reload sequence handle_api_switch runs (the line
            # that used to call the removed _init_style_overrides).
            reproduced, _ = fr.reproduce(recipe)
            editor.fig = reproduced
            editor._overrides = None
            img, _bboxes, _size = render_with_overrides(
                editor.fig, editor.get_effective_style(), editor.dark_mode
            )
            # Assert -- a real image came back (no AttributeError, no blank).
            assert img

    def test_effective_style_is_dict_after_overrides_reset(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            recipe = Path(tmpdir) / "fig.yaml"
            fig, ax = fr.subplots()
            ax.plot([1, 2, 3], [4, 5, 6])
            fr.save(fig, recipe, validate=False, verbose=False)
            editor = get_or_create_editor(f"k2_{recipe}", str(recipe))
            # Act -- reset overrides then read the effective style (lazy rebuild).
            editor._overrides = None
            style = editor.get_effective_style()
            # Assert
            assert isinstance(style, dict)


class TestNoStaleInitStyleOverrides:
    def test_handlers_module_has_no_init_style_overrides_caller(self):
        # Arrange -- read the handler source by PATH; importing the handlers
        # package pulls in scitex_app's Django models and needs configured
        # settings. The removed method must not be referenced.
        import figrecipe

        files_py = Path(figrecipe.__file__).parent / "_django" / "handlers" / "files.py"
        source = files_py.read_text(encoding="utf-8")
        # Act
        has_stale_call = "_init_style_overrides" in source
        # Assert
        assert not has_stale_call

    def test_editorstate_has_no_init_style_overrides_attr(self):
        # Arrange
        from figrecipe._django.services import EditorState

        editor = EditorState()
        # Act
        has_attr = hasattr(editor, "_init_style_overrides")
        # Assert
        assert not has_attr
