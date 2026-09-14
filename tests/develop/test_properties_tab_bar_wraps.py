#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The properties-panel tab bar must wrap, not clip, at narrow widths.

Live-audit finding #2 (scitex-hub, /apps/figrecipe/ 1440px viewport, TODO 125
adjacent): .properties-tabs was display:flex with flex-shrink:0 and NO overflow
control, so the tab row (Current/Preset/Layout/View) extended to x=1512 and
clipped the last tab(s). The fix is flex-wrap:wrap on the tab bar.

Source-conformance gate (same species as test_mobile_figure_export_no_label_
overlap.py / test__frontend_css_tokens_resolve.py): reads the stylesheet and
verifies the rule actually landed, because a missing flex-wrap fails silently
(no build error, no console warning) and only shows up as a clipped tab on a
narrow viewport.
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROPS = _REPO_ROOT / "src" / "figrecipe" / "_django" / "frontend" / "src" / "styles" / "panels" / "properties.css"


def test_properties_tab_bar_wraps_instead_of_clipping():
    # Arrange
    css = _PROPS.read_text(encoding="utf-8")
    # Act
    rules = re.findall(r"\.properties-tabs\s*\{([^}]*)\}", css)
    # Assert
    assert any(re.search(r"flex-wrap\s*:\s*wrap", body) for body in rules), (
        ".properties-tabs must set flex-wrap:wrap so the tab row wraps on a "
        "narrow panel instead of clipping the last tab (live-audit #2, 1440px "
        f"viewport). Found rules: {rules}"
    )


def test_properties_tab_bar_is_flex():
    # Arrange: the wrap fix is only meaningful on a flex row.
    css = _PROPS.read_text(encoding="utf-8")
    # Act
    rules = re.findall(r"\.properties-tabs\s*\{([^}]*)\}", css)
    # Assert
    assert any(re.search(r"display\s*:\s*flex", body) for body in rules), (
        ".properties-tabs must remain a flex row (flex-wrap only wraps flex "
        f"items). Found rules: {rules}"
    )
