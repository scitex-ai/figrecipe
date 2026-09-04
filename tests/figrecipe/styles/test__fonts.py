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
    family = mpl.rcParams["font.family"]
    # generic は先頭のまま。CJK フォントがある環境では末尾に足される
    # （日本語をグリフ単位でフォールバックさせるため）。
    assert family[0] == "sans-serif" and sans[0] == "Arial" and "DejaVu Sans" in sans
    cjk = _fonts.cjk_font()
    if cjk is not None:
        assert family[-1] == cjk


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


def test_japanese_labels_render_without_missing_glyphs():
    """日本語ラベルが豆腐にならないこと。

    Latin フォントを単一で固定するとグリフ単位のフォールバックが効かず、
    CJK が全て欠落する。font.family をリストにする修正の回帰テスト。
    CJK フォントが無い環境では検証できないので skip する。
    """
    import warnings

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if _fonts.cjk_font() is None:
        import pytest

        pytest.skip("no CJK font installed")

    ensure_font_family("Arial")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, ax = plt.subplots()
        ax.set_title("売上と経費")
        ax.set_xlabel("月")
        fig.canvas.draw()
        missing = [w for w in caught if "missing from font" in str(w.message)]
    plt.close(fig)
    assert not missing, "Japanese glyphs missing: %d" % len(missing)
