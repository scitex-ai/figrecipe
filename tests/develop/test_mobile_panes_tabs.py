#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phones select permanent labeled panes through the canonical SDK controller.

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


def _pane_declarations(source: str) -> list[tuple[str, str, int]]:
    """Read IDs, translated labels and order from the actual pane markup."""
    return [
        (pane, label, int(order))
        for pane, label, order in re.findall(
            r'paneAttrs\("(\w+)", gettext\("([^"]+)"\), (\d+)\)', source,
        )
    ]


def test_editor_declares_the_four_phone_tabs():
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    adapter = (_FRONTEND / "components" / "mobilePanes.ts").read_text(
        encoding="utf-8"
    )
    css = (_FRONTEND / "styles" / "mobile.css").read_text(encoding="utf-8")
    # Act
    # IDs/labels/order feed SDK-owned tab buttons and their ARIA selection.
    checks = (
        _pane_declarations(source),
        'data-stx-panes="figrecipe"' in source,
        'data-stx-active={phonePane}' in source,
        '"data-stx-label": label' in source,
        'mountPanes as mountSdkPanes' in adapter,
        'from "@scitex/sdk/ui/ts/app/panes"' in adapter,
        'import "@scitex/sdk/ui/css/app/panes.css"' in adapter,
        'mountSdkPanes(host).find((item) => item.root === body)' in adapter,
        'currentEditor?.root.isConnected' in adapter,
        'currentEditor.show(pane)' in adapter,
        bool(re.search(
            r'\.inner-editor__tabs\s*\{\s*display:\s*none;', _phone_block(css)
        )),
        '.stx-panes__tab[aria-selected="true"]' in _phone_block(css),
    )
    # Assert
    assert checks == (
        [("data", "Data", 1), ("plot", "Plot", 2),
         ("figure", "Figure", 3), ("details", "Details", 4)],
        *([True] * 11),
    )


@pytest.mark.parametrize(
    "tab,page_class",
    [
        ("data", "data-page"),
        ("plot", "editor-plot-page"),
        ("canvas", "editor-figure-page"),
    ],
)
def test_each_desktop_page_retains_the_permanent_phone_panes(tab, page_class):
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    css = (_FRONTEND / "styles" / "layout.css").read_text(encoding="utf-8")
    body = source.split('data-stx-active={phonePane}', 1)[1].split(
        "{loading &&", 1
    )[0]
    # Act
    # Page switches hide existing desktop nodes; they never replace the four
    # children collected by SDK panes. Details stays beside each desktop page.
    checks = (
        [pane for pane, _label, _order in _pane_declarations(body)],
        not bool(re.search(r'\{[^{}\n]*&&\s*\(', body)),
        f'onClick={{() => selectTab("{tab}")}}' in source,
        'setActiveTab(tab);' in source,
        'showEditorPane(tab === "canvas" ? "figure" : tab);' in source,
        bool(re.search(
            r'@media \(min-width: 641px\)\s*\{[^}]*'
            + re.escape(
                f'.inner-editor:not([data-editor-tab="{tab}"]) '
                f'.editor-body > .{page_class}'
            ) + r'[^}]*display:\s*none;', css,
        )),
        not bool(re.search(
            r'\[data-editor-tab[^}]*\.stx-layout-most-right', css
        )),
    )
    # Assert
    assert checks == (["data", "plot", "figure", "details"], *([True] * 6))
