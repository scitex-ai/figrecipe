#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brand-triggered global style application.

When a parent package sets ``FIGRECIPE_BRAND`` to a known brand (currently
only ``"scitex.plt"``), importing figrecipe auto-applies that brand's house
plotting style globally — registering fonts, pushing rcParams, and setting
the colour cycle — so that even plain ``plt.subplots()`` / ``plt.plot()``
calls follow the preset, without the parent needing its own auto-config.

This makes ``scitex.plt`` a pure zero-code alias to figrecipe: the parent only
sets ``os.environ["FIGRECIPE_BRAND"] = "scitex.plt"`` before importing.

Plain ``import figrecipe`` (default brand ``"figrecipe"``) is unaffected: this
module is a no-op unless a recognised brand is set. Application is idempotent
and best-effort — any failure is swallowed so it can never break import.
"""

from __future__ import annotations

# Brands that should auto-apply the SCITEX house style on import.
_SCITEX_BRANDS = frozenset({"scitex.plt"})

# Guard so repeated imports / reloads don't re-run the side effects.
_APPLIED = False


def apply_brand_style(brand: str) -> bool:
    """Apply the global house style for *brand*, once.

    Parameters
    ----------
    brand : str
        Value of ``FIGRECIPE_BRAND``.

    Returns
    -------
    bool
        True if a brand style was applied, False if *brand* is unrecognised
        or the style was already applied.
    """
    global _APPLIED

    if _APPLIED:
        return False
    if brand not in _SCITEX_BRANDS:
        return False

    try:
        import matplotlib as mpl
        import matplotlib.pyplot as plt

        from ._configure_mpl import configure_mpl
        from .styles import load_style
        from .styles._fonts import register_arial_fonts

        # 1. Load the SCITEX preset into the global style cache so that
        #    figrecipe.subplots() and configure_mpl() resolve its values.
        try:
            load_style("SCITEX")
        except Exception:
            pass

        # 2. Register Arial (publication default) and pin the font family.
        arial_ok = register_arial_fonts()
        if arial_ok:
            mpl.rcParams["font.family"] = "Arial"
            mpl.rcParams["font.sans-serif"] = [
                "Arial",
                "Helvetica",
                "DejaVu Sans",
                "Liberation Sans",
            ]
        else:
            mpl.rcParams["font.family"] = "sans-serif"
            mpl.rcParams["font.sans-serif"] = [
                "Helvetica",
                "DejaVu Sans",
                "Liberation Sans",
                "sans-serif",
            ]
            import logging

            logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

        # 3. Push the bulk of the rcParams + colour cycle via figrecipe's own
        #    global configurer (autolayout=True matches the scitex original).
        configure_mpl(plt, autolayout=True)

        # 4. Mathtext defaults (not covered by configure_mpl).
        mpl.rcParams["mathtext.fontset"] = "dejavusans"
        mpl.rcParams["mathtext.default"] = "regular"

        _APPLIED = True
        return True
    except Exception:
        # Never let styling break `import figrecipe`.
        return False


# EOF
