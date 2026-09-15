#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hub phones show the editor as tabs (scitex-ui panes), without collapse title bars.

The operator saw the collapsible "Viewer" bar leave an empty area that read as a
broken image; on phones only the pane tabs switch columns.
"""

import re
from pathlib import Path

_FRONTEND = Path(__file__).resolve().parents[2] / "src" / "figrecipe" / "_django" / "frontend" / "src"


def _phone_block(css: str) -> str:
    start = css.index("@media (max-width: 640px)")
    depth = 0
    for i in range(css.index("{", start), len(css)):
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        if depth == 0:
            return css[start:i]
    return ""


def test_phone_panes_hide_collapse_title_bars():
    # Arrange
    css = (_FRONTEND / "styles" / "mobile.css").read_text(encoding="utf-8")
    # Act
    block = _phone_block(css)
    # Assert
    assert re.search(r"\.stx-panes--single \.pane-header--minimal[^{]*\{[^}]*display:\s*none", block), (
        "phones must not show the collapsible viewer title bar"
    )


def test_editor_declares_the_four_phone_tabs():
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    # Act
    panes = re.findall(r'paneAttrs\("(\w+)"', source)
    # Assert
    assert panes == ["data", "plot", "figure", "details"], f"pane ids in DOM order: {panes}"
