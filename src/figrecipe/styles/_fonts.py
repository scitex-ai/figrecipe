#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Font utilities for figrecipe.

Provides font availability checking and listing for publication-quality figures.
"""

__all__ = [
    "list_available_fonts",
    "check_font",
    "register_arial_fonts",
]

import os
import warnings
from typing import List


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
