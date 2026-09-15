#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The figure Export control must not clip the figure title on mobile.

2026-09-15: phones now show a labelled primary Export button (operator: the
flow must be self-explanatory); the figure is pushed below its row instead of
hiding the label.

PR #381 added a labelled "⬇ Export" pill to FigureViewer (top-right of the
figure surface). At ≤768px the figure fills the viewport, so the labelled pill
stretches left across the figure's title — measured live on the deployed route
(figrecipe-mobile-visual-polish-20260914). The fix makes the control
icon-only inside the mobile media block: the label ``<span>`` is hidden and the
padding/gap collapse, while ``title`` / ``aria-label`` keep the action
named for screen readers.

Lives in ``tests/develop/`` next to ``test__frontend_css_tokens_resolve.py`` —
the same species: a source-conformance gate that reads the stylesheet and asks
"did the rule actually land?", because a missing or mis-scoped ``display:none``
fails silently (no build error, no console warning) and only shows up as a
clipped title on a phone.
"""

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MOBILE = _REPO_ROOT / "src" / "figrecipe" / "_django" / "frontend" / "src" / "styles" / "mobile.css"
_LAYOUT = _REPO_ROOT / "src" / "figrecipe" / "_django" / "frontend" / "src" / "styles" / "layout.css"


def _mobile_media_block(css: str) -> str:
    """The body of the first @media (max-width: 768px) block, braces matched."""
    m = re.search(r"@media\s*\(\s*max-width\s*:\s*768px\s*\)\s*\{", css)
    if not m:
        pytest.fail("mobile.css has no @media (max-width: 768px) block")
    depth = 0
    for i in range(m.end() - 1, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[m.end() : i]
    pytest.fail("unbalanced braces in the mobile media block")


def _rules(selector_fragment: str, block: str) -> list[str]:
    """All rule bodies whose selector contains ``selector_fragment``."""
    return re.findall(
        r"([^{}]*" + re.escape(selector_fragment) + r"[^{}]*)\{([^}]*)\}", block
    )


def test_mobile_media_block_exists():
    # Arrange
    css = _MOBILE.read_text(encoding="utf-8")
    # Act
    block = _mobile_media_block(css)
    # Assert
    assert len(block.strip()) > 0, "mobile media block is empty"


def test_mobile_export_control_keeps_its_label():
    # Arrange
    block = _mobile_media_block(_MOBILE.read_text(encoding="utf-8"))
    # Act
    hides = [body for _, body in _rules(".figure-viewer__export span", block) if re.search(r"display\s*:\s*none", body)]
    # Assert
    assert not hides, "phones get a visible, labelled Export button"


def test_mobile_figure_sits_below_the_export_button():
    # Arrange
    block = _mobile_media_block(_MOBILE.read_text(encoding="utf-8"))
    # Act
    bodies = [body for sel, body in _rules(".figure-viewer:has(.figure-viewer__export)", block)]
    # Assert
    assert any(re.search(r"padding-top\s*:\s*\d+px", b) for b in bodies), (
        f"the figure must be pushed below the Export button's row so the label cannot cover the title. Found: {bodies}"
    )


def test_desktop_export_control_stays_labelled():
    """The icon-only collapse is MOBILE-only.

    On a wide canvas the labelled pill sits in empty space (measured: no
    overlap at 1280px), so hiding the label there would make the control
    ambiguous. The desktop rule in layout.css must NOT hide the span.
    """
    # Arrange
    layout = _LAYOUT.read_text(encoding="utf-8")
    # Act
    desktop_hide = re.search(
        r"\.figure-viewer__export\s+span\s*\{\s*display\s*:\s*none", layout
    )
    # Assert
    assert not desktop_hide, (
        "layout.css hides the export label on desktop — the icon-only rule "
        "belongs to the mobile media block only"
    )
