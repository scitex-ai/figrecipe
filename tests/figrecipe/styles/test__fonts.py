#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe.styles._fonts (Arial default + loud DejaVu fallback)."""

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import pytest

from figrecipe.styles import _fonts
from figrecipe.styles._fonts import ensure_font_family, font_is_available


def test_import_styles__fonts_module():
    # Arrange
    module_path = "figrecipe.styles._fonts"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_ensure_font_family_prefers_requested_with_dejavu_fallback():
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    # Act
    ensure_font_family("Arial")
    sans = mpl.rcParams["font.sans-serif"]
    # Assert
    assert (
        mpl.rcParams["font.family"] == ["sans-serif"]
        and sans[0] == "Arial"
        and "DejaVu Sans" in sans
    )


def test_absent_font_is_reported_unavailable():
    # Arrange
    absent = "NoSuchFontXYZ123"
    # Act
    available = font_is_available(absent)
    # Assert
    assert available is False


def test_loud_warning_fires_once_when_preferred_font_absent():
    # Arrange
    absent = "NoSuchFontXYZ123"
    _fonts._FALLBACK_WARNED.clear()
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ensure_font_family(absent)
        ensure_font_family(absent)
    fr_warnings = [w for w in caught if "figrecipe: font" in str(w.message)]
    # Assert
    assert len(fr_warnings) == 1
