#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""An unknown style key must be audible, not silently dropped.

Card figrecipe-three-style-key-vocabularies-disagree-20260907: three vocabularies
disagree (the loaded style's, ``SCITEX_STYLE``'s 33 advertised keys, and the
layout path's), so a MISSPELLED key matches nothing anywhere and the merge in
``_api/_subplots.py`` carries it without a word — the caller sees a figure that
simply did not change. These tests pin the detector that turns that into a
message, and the near-miss suggestion that makes the fix one word.

Each test makes a single assertion (STX-TQ007); no mocks (PA-306).
"""

import warnings
from pathlib import Path

from figrecipe.styles._style_keys import (
    UnknownStyleKeyWarning,
    style_key_suggestions,
    unknown_style_keys,
    warn_unknown_style_keys,
)

KNOWN = ["font_family", "axes_thickness_mm", "margin_left_mm", "grid"]


class TestUnknownStyleKeys:
    def test_a_key_no_consumer_knows_is_reported(self):
        # Arrange
        style = {"font_famly": "Arial"}
        # Act
        unknown = unknown_style_keys(style, KNOWN)
        # Assert
        assert unknown == ["font_famly"]

    def test_a_known_key_is_not_reported(self):
        # Arrange
        style = {"font_family": "Arial", "margin_left_mm": 15}
        # Act
        unknown = unknown_style_keys(style, KNOWN)
        # Assert
        assert unknown == []


class TestSuggestions:
    def test_a_misspelling_is_matched_to_the_key_it_meant(self):
        # Arrange
        style = {"font_famly": "Arial"}
        # Act
        suggestions = style_key_suggestions(style, KNOWN)
        # Assert
        assert suggestions == {"font_famly": "font_family"}

    def test_a_genuinely_new_key_gets_no_misleading_suggestion(self):
        # Arrange
        style = {"qt_style_sheet": "x"}
        # Act
        suggestions = style_key_suggestions(style, KNOWN)
        # Assert
        assert suggestions == {}


class TestTheWarning:
    def test_the_warning_names_the_key_and_what_it_meant(self):
        # Arrange
        style = {"font_famly": "Arial"}
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warned = warn_unknown_style_keys(style, KNOWN)
        message = str(caught[0].message) if caught else ""
        # Assert
        assert warned == ["font_famly"] and "font_family" in message

    def test_a_known_style_is_silent(self):
        # Arrange
        style = {"font_family": "Arial"}
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warned = warn_unknown_style_keys(style, KNOWN)
        # Assert -- a warning here would be a false alarm on the ordinary path.
        assert warned == [] and not caught


class TestModuleHygiene:
    def test_the_module_stays_dependency_free(self):
        # Arrange
        source = Path(__file__).resolve().parents[3]
        module = source / "src" / "figrecipe" / "styles" / "_style_keys.py"
        # Act
        text = module.read_text(encoding="utf-8")
        # Assert -- it must run under the repo's expression tests, so no package
        # imports and no React/UI layer.
        assert "from figrecipe" not in text and "import figrecipe" not in text

    def test_the_warning_class_is_a_user_warning(self):
        # Arrange
        warning_class = UnknownStyleKeyWarning
        # Act
        is_user_warning = issubclass(warning_class, UserWarning)
        # Assert -- callers filtering UserWarning must not miss it.
        assert is_user_warning
