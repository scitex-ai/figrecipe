#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The figure preview must stay visible above the scitex-hub site dock at 390px.

Site-audit D15: on the hub the stacked mobile layout put the 56px-wide
plot-type rail (~530px tall as a column) above the preview, pushing the
preview below the viewport and under the hub's fixed site dock. The fix
orders the preview first, turns the rail into a horizontal strip, and gives
the preview a scroll margin equal to the hub's ``--site-dock-height``
(0 in standalone, where no dock exists).

Same species as ``test_mobile_figure_export_no_label_overlap.py``: a
source-conformance gate, because a missing rule fails silently and only
shows up as a hidden figure on a phone.
"""

import re
from pathlib import Path

import pytest

_STYLES = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "frontend"
    / "src"
    / "styles"
)
_MOBILE = _STYLES / "mobile.css"
_LAYOUT = _STYLES / "layout.css"


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


def _rule_bodies(selector: str, css: str) -> list[str]:
    """Bodies of rules whose selector list contains exactly ``selector``."""
    bodies = []
    for selectors, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        names = [s.strip() for s in re.sub(r"/\*.*?\*/", "", selectors, flags=re.S).split(",")]
        if selector in names:
            bodies.append(body)
    return bodies


def test_preview_reserves_hub_dock_height_with_standalone_fallback():
    # Arrange
    layout = _LAYOUT.read_text(encoding="utf-8")
    # Act
    bodies = _rule_bodies(".split-pane-center", layout)
    # Assert
    assert any(
        re.search(
            r"scroll-margin-bottom\s*:\s*calc\(\s*var\(\s*--site-dock-height\s*,\s*0px\s*\)"
            r"\s*\+\s*env\(\s*safe-area-inset-bottom",
            body,
        )
        for body in bodies
    ), f"layout.css .split-pane-center must reserve var(--site-dock-height, 0px) + safe area. Found: {bodies}"


def test_mobile_orders_preview_before_data():
    # Arrange
    block = _mobile_media_block(_MOBILE.read_text(encoding="utf-8"))
    order = lambda sel: [int(m) for b in _rule_bodies(sel, block) for m in re.findall(r"order\s*:\s*(-?\d+)", b)]
    # Act
    center, left = order(".split-pane-center"), order(".split-pane-left")
    # Assert
    assert center and left and center[0] < left[0], f"preview must come before Data on phones: {center} vs {left}"


def test_mobile_editor_body_scrolls_instead_of_squeezing():
    # Arrange
    block = _mobile_media_block(_MOBILE.read_text(encoding="utf-8"))
    # Act
    bodies = _rule_bodies(".editor-body", block)
    # Assert
    assert any(re.search(r"overflow-y\s*:\s*auto", b) and re.search(r"padding-bottom\s*:", b) for b in bodies), (
        f"mobile .editor-body must scroll with end padding so no section is squeezed or hidden. Found: {bodies}"
    )


def test_mobile_plot_type_rail_is_horizontal():
    # Arrange
    block = _mobile_media_block(_MOBILE.read_text(encoding="utf-8"))
    # Act
    bodies = _rule_bodies(".plot-type-nav .stx-app-selector-nav", block)
    # Assert
    assert any(
        re.search(r"flex-direction\s*:\s*row", body)
        and re.search(r"max-width\s*:\s*100%\s*!important", body)
        for body in bodies
    ), (
        "mobile selector nav must lay out as a row and override the inline 56px "
        f"max-width with !important. Found: {bodies}"
    )


def test_desktop_plot_type_rail_stays_vertical():
    # Arrange
    css = (_STYLES / "panels" / "plot-type-nav.css").read_text(encoding="utf-8")
    # Act
    bodies = _rule_bodies(".plot-type-nav", css)
    # Assert
    assert any(re.search(r"flex-direction\s*:\s*column", body) for body in bodies), (
        "the desktop .plot-type-nav rule must stay a vertical column; the row "
        "layout belongs to the mobile media block only"
    )
