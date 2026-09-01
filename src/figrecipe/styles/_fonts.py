#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Font utilities for figrecipe.

Provides font availability checking and listing for publication-quality figures.
"""

__all__ = [
    "list_available_fonts",
    "check_font",
    "register_arial_fonts",
    "ensure_font_family",
    "font_is_available",
]

import os
import warnings
from typing import List, Optional

# Guaranteed-present fallback chain after the preferred font. DejaVu Sans ships
# with matplotlib, so it is always resolvable even on font-less CI/Docker boxes.
_SANS_FALLBACKS = ["DejaVu Sans", "Liberation Sans", "Helvetica", "sans-serif"]

# Fonts for which the loud "not installed -> falling back" warning has already
# been emitted this session. Keyed by font name so the warning fires exactly
# ONCE per missing font (not per glyph, not per axes, not per figure). Cleared
# only on interpreter restart.
_FALLBACK_WARNED: set = set()


def register_arial_fonts() -> bool:
    """Register Arial fonts from the system if available.

    Searches the system font directories for any ``arial*`` font file and
    registers it with matplotlib's font manager so ``font.family = "Arial"``
    resolves correctly. Safe to call repeatedly (idempotent).

    Returns
    -------
    bool
        True if Arial is available after registration, False otherwise.
    """
    import matplotlib.font_manager as fm

    try:
        fm.findfont("Arial", fallback_to_default=False)
        return True
    except Exception:
        arial_paths = [
            f
            for f in fm.findSystemFonts()
            if os.path.basename(f).lower().startswith("arial")
        ]
        for path in arial_paths:
            try:
                fm.fontManager.addfont(path)
            except Exception:
                pass
        try:
            fm.findfont("Arial", fallback_to_default=False)
            return True
        except Exception:
            return False


def list_available_fonts() -> List[str]:
    """List all available font families.

    Returns
    -------
    list of str
        Sorted list of available font family names.

    Examples
    --------
    >>> fonts = ps.list_available_fonts()
    >>> print(fonts[:5])
    ['Arial', 'Courier New', 'DejaVu Sans', ...]
    """
    import matplotlib.font_manager as fm

    fonts = set()
    for font in fm.fontManager.ttflist:
        fonts.add(font.name)
    return sorted(fonts)


def check_font(font_family: str, fallback: str = "DejaVu Sans") -> str:
    """Check if font is available, with fallback chain.

    Parameters
    ----------
    font_family : str
        Requested font family name.
    fallback : str
        Fallback font if requested font is not available.

    Returns
    -------
    str
        The font to use (original if available, fallback otherwise).

    Examples
    --------
    >>> font = check_font("Arial")  # Returns "Arial" if available
    >>> font = check_font("NonExistentFont")  # Returns fallback with warning
    """

    available = list_available_fonts()

    if font_family in available:
        return font_family

    # Try a fallback chain: common sans-serif fonts
    _FALLBACK_CHAIN = ["Arial", "Liberation Sans", "DejaVu Sans"]
    for candidate in _FALLBACK_CHAIN:
        if candidate != font_family and candidate in available:
            warnings.warn(
                f"Font '{font_family}' not found, using '{candidate}'",
                UserWarning,
            )
            return candidate

    # Last resort
    if fallback in available:
        warnings.warn(
            f"Font '{font_family}' not found, using fallback '{fallback}'",
            UserWarning,
        )
        return fallback

    return "DejaVu Sans"


#: 日本語グリフを持つフォントの候補。先頭から最初に見つかったものを使う。
_CJK_CANDIDATES = (
    "IPAexGothic",
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "Source Han Sans JP",
    "TakaoPGothic",
    "IPAGothic",
    "VL PGothic",
)


def cjk_font() -> Optional[str]:
    """Return the first available CJK-capable family, or None.

    Latin faces such as Arial carry no CJK glyphs, so a figure whose labels
    are Japanese renders as tofu unless a CJK face is offered alongside.
    """
    available = set(list_available_fonts())
    for candidate in _CJK_CANDIDATES:
        if candidate in available:
            return candidate
    return None


def font_family_chain(preferred: str) -> List[str]:
    """Return ``[preferred, <cjk fallback>]`` for per-glyph fallback.

    matplotlib falls back glyph-by-glyph only when the family is a LIST;
    pinning a single family defeats it.
    """
    chain = [check_font(preferred)]
    cjk = cjk_font()
    if cjk and cjk not in chain:
        chain.append(cjk)
    return chain


def font_is_available(font_family: str) -> bool:
    """Return True if matplotlib's font manager resolves *font_family* exactly.

    Uses ``findfont(..., fallback_to_default=False)`` so a missing font raises
    instead of silently resolving to DejaVu Sans -- i.e. this answers "is the
    EXACT font installed?", not "can matplotlib draw something?".

    Parameters
    ----------
    font_family : str
        Font family name to probe (e.g. ``"Arial"``).
    """
    import matplotlib.font_manager as fm

    try:
        fm.findfont(font_family, fallback_to_default=False)
        return True
    except Exception:
        return False


def ensure_font_family(preferred: str = "Arial") -> bool:
    """Pin *preferred* as the figure font, with a loud DejaVu Sans fallback.

    Sets ``font.family = ['sans-serif', <cjk>]`` -- the CJK face is appended
    so matplotlib falls back GLYPH BY GLYPH for Japanese/Chinese text, which a
    single pinned family cannot do -- and puts *preferred*
    first in ``font.sans-serif`` followed by a guaranteed-present fallback
    chain (DejaVu Sans ships with matplotlib). Registers Arial from system
    font dirs first so a freshly-installed Arial is picked up.

    If *preferred* is NOT resolvable by the font manager, emits ONE loud
    figrecipe warning (per missing font, per session) so the user knows their
    figures are rendering in the fallback rather than the requested font --
    the project's NO-SILENT-FALLBACK rule. Never raises.

    Parameters
    ----------
    preferred : str
        Preferred font family (default ``"Arial"``).

    Returns
    -------
    bool
        True if *preferred* is available (exact match), False if the figure
        will render in the fallback font.
    """
    import matplotlib as mpl

    if preferred == "Arial":
        # Best-effort pick-up of a system Arial before probing availability.
        register_arial_fonts()

    # Build font.sans-serif = [preferred, <guaranteed fallbacks...>], deduped
    # while preserving order so the preferred font always wins when present.
    chain: List[str] = []
    for name in [preferred, *_SANS_FALLBACKS]:
        if name not in chain:
            chain.append(name)

    # font.family をリストにすると matplotlib がグリフ単位でフォールバックする。
    # generic を先頭に置き、CJK を後ろに足す。凡例など apply_style が触らない
    # テキストも含めて日本語が出るようになる。
    _cjk = cjk_font()
    _fam = ["sans-serif"]
    if _cjk:
        _fam.append(_cjk)
    mpl.rcParams["font.family"] = _fam
    # CJK グリフは Latin フォントに無い。チェーン末尾に CJK フォントを足して
    # matplotlib のグリフ単位フォールバックに拾わせる（豆腐を防ぐ）。
    if _cjk and _cjk not in chain:
        chain = list(chain) + [_cjk]
    mpl.rcParams["font.sans-serif"] = chain

    available = font_is_available(preferred)
    if not available:
        fallback = next(
            (f for f in _SANS_FALLBACKS if font_is_available(f)),
            "DejaVu Sans",
        )
        if preferred not in _FALLBACK_WARNED:
            _FALLBACK_WARNED.add(preferred)
            _warn_font_fallback(preferred, fallback)

    return available


def _warn_font_fallback(preferred: str, fallback: str) -> None:
    """Emit the single loud figrecipe font-fallback warning.

    Routed through both ``warnings.warn`` (so ``pytest.warns`` / ``-W`` see it)
    and figrecipe's logger (so it shows up in console output alongside other
    figrecipe status lines). Matplotlib's own per-glyph ``findfont`` spam is
    suppressed -- THIS is the one authoritative notice.
    """
    import logging

    msg = (
        f"figrecipe: font {preferred!r} is not installed; figures will "
        f"render in {fallback!r}. Install {preferred} for an exact match."
    )
    # Silence matplotlib's per-glyph findfont fallback log; our single warning
    # is the authoritative, deduped notice (avoids the unreadable spam).
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

    warnings.warn(msg, UserWarning, stacklevel=2)
    try:
        from .._logging import get_logger

        get_logger().warning(msg)
    except Exception:  # logger is best-effort; the warnings.warn already fired
        pass
