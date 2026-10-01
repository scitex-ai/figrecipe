#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hub phones show the editor as tabs (scitex-ui panes), without collapse title bars.

The operator saw the collapsible "Viewer" bar leave an empty area that read as a
broken image; on phones only the pane tabs switch columns.
"""

import re
from pathlib import Path

import pytest

_FRONTEND = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "frontend"
    / "src"
)


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
    assert re.search(
        r"\.stx-panes--single \.pane-header--minimal[^{]*\{[^}]*display:\s*none", block
    ), "phones must not show the collapsible viewer title bar"


def _tab_content_blocks(source: str) -> dict[str, str]:
    """Read the real mutually exclusive active-tab contents from the JSX."""
    blocks = {}
    for match in re.finditer(r'\{activeTab === "(data|plot|canvas)" && \(\n', source):
        end = source.index("\n        )}", match.end())
        blocks[match.group(1)] = source[match.end() : end]
    return blocks


def test_editor_declares_the_four_phone_tabs():
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    # Act
    # Canvas occupies the Figure pane only when its alternate tab is active.
    # The logical pane vocabulary/order is the existing four-pane contract.
    source = source.replace(_tab_content_blocks(source)["canvas"], "")
    panes = re.findall(r'paneAttrs\("(\w+)"', source)
    # Assert
    assert panes == ["data", "plot", "figure", "details"], (
        f"pane ids in DOM order: {panes}"
    )


@pytest.mark.parametrize(
    "tab,expected",
    [
        ("data", ["data", "details"]),
        ("plot", ["plot", "figure", "details"]),
        ("canvas", ["figure", "details"]),
    ],
)
def test_each_active_tab_declares_only_its_visible_phone_panes(tab, expected):
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    branches = _tab_content_blocks(source)
    # Act
    visible = source
    for mode, body in branches.items():
        if mode != tab:
            visible = visible.replace(body, "")
    panes = re.findall(r'paneAttrs\("(\w+)"', visible)
    # Assert
    assert panes == expected, f"active {tab} pane ids in DOM order: {panes}"
