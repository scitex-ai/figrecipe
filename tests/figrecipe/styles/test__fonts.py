#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe.styles._fonts: Arial default, loud fallback, CJK chain.

The CJK half pins the MECHANISM in every environment, not only where a CJK
font happens to be installed: matplotlib falls back glyph-by-glyph only when
``font.family`` is a LIST, and that is demonstrated below with two fonts that
ship inside matplotlib itself (STIXSizeOneSym carries a handful of glyphs;
DejaVu Sans carries Latin). The Japanese render test still runs wherever a CJK
face exists, and skips -- visibly -- where none does.

No fixture patches process state: the env-var tests set and pop the variable
themselves, and the warning helper takes the resolved family as an argument.
"""

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from figrecipe.styles import _fonts
from figrecipe.styles._fonts import (
    CJK_FONT_ENV,
    cjk_font,
    ensure_font_family,
    font_family_chain,
    font_is_available,
    has_cjk,
    reset_cjk_font_cache,
    warn_if_cjk_without_font,
)

_ABSENT = "NoSuchFontXYZ123"
_BUNDLED_SPARSE = "STIXSizeOneSym"  # ships with matplotlib; very few glyphs
_BUNDLED_LATIN = "DejaVu Sans"  # ships with matplotlib; full Latin


def test_import_styles__fonts_module():
    # Arrange
    module_path = "figrecipe.styles._fonts"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# ── ensure_font_family: generic first, requested font first in sans-serif ─────


@pytest.fixture
def _arial_applied():
    _fonts._FALLBACK_WARNED.clear()
    reset_cjk_font_cache()
    ensure_font_family("Arial")
    yield
    reset_cjk_font_cache()


def test_ensure_font_family_keeps_generic_family_first(_arial_applied):
    # Arrange
    family = mpl.rcParams["font.family"]
    # Act
    first = family[0]
    # Assert
    assert first == "sans-serif"


def test_ensure_font_family_makes_family_a_list(_arial_applied):
    """A bare string defeats per-glyph fallback; the family must be a list."""
    # Arrange
    family = mpl.rcParams["font.family"]
    # Act
    kind = type(family)
    # Assert
    assert kind is list


def test_ensure_font_family_puts_requested_font_first_in_sans_serif(_arial_applied):
    # Arrange
    sans = mpl.rcParams["font.sans-serif"]
    # Act
    first = sans[0]
    # Assert
    assert first == "Arial"


def test_ensure_font_family_keeps_dejavu_fallback_in_sans_serif(_arial_applied):
    # Arrange
    sans = mpl.rcParams["font.sans-serif"]
    # Act
    present = _BUNDLED_LATIN in sans
    # Assert
    assert present


@pytest.fixture
def _cjk_face_present():
    """The resolved CJK family, or a visible skip where none is installed."""
    reset_cjk_font_cache()
    cjk = cjk_font()
    if cjk is None:
        pytest.skip("no CJK font installed here")
    return cjk


def test_ensure_font_family_appends_cjk_face_when_one_exists(
    _arial_applied, _cjk_face_present
):
    # Arrange
    cjk = _cjk_face_present
    # Act
    last = mpl.rcParams["font.family"][-1]
    # Assert
    assert last == cjk


def test_absent_font_is_reported_unavailable():
    # Arrange
    absent = _ABSENT
    # Act
    available = font_is_available(absent)
    # Assert
    assert available is False


def test_loud_warning_fires_once_when_preferred_font_absent():
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ensure_font_family(_ABSENT)
        ensure_font_family(_ABSENT)
    fr_warnings = [w for w in caught if "figrecipe: font" in str(w.message)]
    # Assert
    assert len(fr_warnings) == 1


# ── font_family_chain ─────────────────────────────────────────────────────────


def test_font_family_chain_starts_with_the_resolved_requested_font():
    # Arrange
    reset_cjk_font_cache()
    # Act
    chain = font_family_chain(_BUNDLED_LATIN)
    # Assert
    assert chain[0] == _BUNDLED_LATIN


def test_font_family_chain_is_a_list():
    # Arrange
    reset_cjk_font_cache()
    # Act
    chain = font_family_chain(_BUNDLED_LATIN)
    # Assert
    assert isinstance(chain, list)


# ── the mechanism, in every environment: list families fall back per glyph ────


def _missing_glyph_warnings(family):
    """Render a Latin string with *family* and count matplotlib's own
    'missing from font' warnings -- an independent instrument, not ours."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Sales and costs", fontfamily=family)
        fig.canvas.draw()
    plt.close(fig)
    return [w for w in caught if "missing from font" in str(w.message)]


def test_control_single_sparse_family_loses_glyphs():
    """Positive control: with ONE sparse family the glyphs go missing."""
    # Arrange
    family = [_BUNDLED_SPARSE]
    # Act
    missing = _missing_glyph_warnings(family)
    # Assert
    assert len(missing) > 0


def test_list_family_falls_back_per_glyph():
    """The fix's whole premise: a LIST family lets matplotlib take each glyph
    from the first family that has it, so nothing goes missing."""
    # Arrange
    family = [_BUNDLED_SPARSE, _BUNDLED_LATIN]
    # Act
    missing = _missing_glyph_warnings(family)
    # Assert
    assert len(missing) == 0


# ── has_cjk ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text",
    ["売上と経費", "月", "テスト", "、", "「」", "％", "９", "한글", "𠀋"],
)
def test_has_cjk_detects_cjk_text(text):
    # Arrange
    sample = text
    # Act
    detected = has_cjk(sample)
    # Assert
    assert detected is True


@pytest.mark.parametrize("text", ["Sales", "42%", "", "café", "Δx"])
def test_has_cjk_ignores_non_cjk_text(text):
    """Negative control: Latin, digits, accents and Greek are not CJK."""
    # Arrange
    sample = text
    # Act
    detected = has_cjk(sample)
    # Assert
    assert detected is False


# ── cjk_font: the env override, exercised with a font that always exists ──────


@pytest.fixture
def _env_names_bundled_latin():
    saved = os.environ.get(CJK_FONT_ENV)
    os.environ[CJK_FONT_ENV] = _BUNDLED_LATIN
    reset_cjk_font_cache()
    yield
    if saved is None:
        os.environ.pop(CJK_FONT_ENV, None)
    else:
        os.environ[CJK_FONT_ENV] = saved
    reset_cjk_font_cache()


@pytest.fixture
def _env_names_absent_font():
    saved = os.environ.get(CJK_FONT_ENV)
    os.environ[CJK_FONT_ENV] = _ABSENT
    _fonts._FALLBACK_WARNED.clear()
    reset_cjk_font_cache()
    yield
    if saved is None:
        os.environ.pop(CJK_FONT_ENV, None)
    else:
        os.environ[CJK_FONT_ENV] = saved
    reset_cjk_font_cache()


def test_cjk_font_honours_env_override_when_installed(_env_names_bundled_latin):
    # Arrange
    expected = _BUNDLED_LATIN
    # Act
    found = cjk_font()
    # Assert
    assert found == expected


def test_cjk_font_warns_when_env_names_an_absent_font(_env_names_absent_font):
    """A declared font that cannot be honoured must not evaporate silently."""
    # Arrange
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        # Act
        cjk_font()
    env_warnings = [w for w in caught if CJK_FONT_ENV in str(w.message)]
    # Assert
    assert len(env_warnings) == 1


# ── warn_if_cjk_without_font, decided from a known state ──────────────────────


def _figure_with(text):
    fig, ax = plt.subplots()
    ax.set_title(text)
    return fig


def test_warns_when_cjk_text_and_no_cjk_face():
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    fig = _figure_with("売上と経費")
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fired = warn_if_cjk_without_font(fig, cjk_family=None)
    plt.close(fig)
    # Assert
    assert fired is True


def test_warning_names_the_env_override(_arial_applied):
    """The warning must say what to DO, not only what broke."""
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    fig = _figure_with("売上と経費")
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_if_cjk_without_font(fig, cjk_family=None)
    plt.close(fig)
    texts = [str(w.message) for w in caught]
    # Assert
    assert any(CJK_FONT_ENV in t for t in texts)


def test_control_no_warning_when_a_cjk_face_is_usable():
    """Negative control: with a CJK face the same figure warns nothing."""
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    fig = _figure_with("売上と経費")
    # Act
    fired = warn_if_cjk_without_font(fig, cjk_family=_BUNDLED_LATIN)
    plt.close(fig)
    # Assert
    assert fired is False


def test_control_no_warning_for_latin_only_text():
    """Negative control: no CJK text, no warning, even with no CJK face."""
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    fig = _figure_with("Sales and costs")
    # Act
    fired = warn_if_cjk_without_font(fig, cjk_family=None)
    plt.close(fig)
    # Assert
    assert fired is False


# ── the Japanese render itself, wherever a CJK face exists ───────────────────


def test_japanese_labels_render_without_missing_glyphs(_cjk_face_present):
    """日本語ラベルが豆腐にならないこと。CJK フォントが無い環境では skip する
    (the mechanism is pinned above regardless)."""
    # Arrange
    _fonts._FALLBACK_WARNED.clear()
    ensure_font_family("Arial")
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, ax = plt.subplots()
        ax.set_title("売上と経費")
        ax.set_xlabel("月")
        fig.canvas.draw()
    plt.close(fig)
    missing = [w for w in caught if "missing from font" in str(w.message)]
    # Assert
    assert len(missing) == 0


# EOF
