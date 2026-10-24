#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure tab: SDK shared align controls + working Rulers/Fit/Export.

Owner batch apps-figrecipe-ui-feedback-20261023 item 4 —
(1) the bespoke Figure Align / Axes Align button grids in Details are gone,
replaced by the SDK SelectorNav (the same shared control the plot-type rail
uses); (2) Toggle Rulers actually hides the rulers (the toggle used to flip
store state nothing read); Fit/zoom stand down until the Figure canvas mounts
and registers its controls (a click before that was a silent no-op).

Source-conformance gates: each property below is pinned to the exact source
that renders it.
"""

import re
from pathlib import Path

_FRONTEND = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "frontend"
    / "src"
)
_PROPS = _FRONTEND / "components" / "Properties" / "Properties.tsx"
_LOCALE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "figrecipe"
    / "_django"
    / "locale"
    / "ja"
    / "LC_MESSAGES"
    / "djangojs.po"
)


def _section(source: str, title: str) -> str:
    """The PropSection body for a Details section title."""
    start = source.index(f'title={{gettext("{title}")}}')
    end = source.index("</PropSection>", start)
    return source[start:end]


def test_align_sections_use_the_shared_selector_nav():
    # Arrange
    source = _PROPS.read_text(encoding="utf-8")
    # Act
    problems = []
    if 'from "@scitex/sdk/ui/react/app/selector-nav"' not in source:
        problems.append("no shared SelectorNav import")
    for title in ("Figure Align", "Axes Align"):
        body = _section(source, title)
        if "SelectorNav" not in body:
            problems.append(f"{title} is not a SelectorNav")
        if "details-btn-grid" in body or "<button" in body:
            problems.append(f"{title} keeps bespoke buttons")
    # Assert
    assert problems == []


def test_align_labels_come_from_the_translated_catalog():
    # Arrange: zero new copy — every align label must already be translated.
    source = _PROPS.read_text(encoding="utf-8")
    catalog = _LOCALE.read_text(encoding="utf-8")
    # Act
    labels = re.findall(r'gettext_noop\("([^"]+)"\)', source)
    align = [label for label in labels if label in ("Left", "Ctr H", "Ax Left", "Ax Bot")]
    missing = [label for label in align if f'msgid "{label}"' not in catalog]
    # Assert
    assert align != [] and missing == [], f"untranslated align labels: {missing}"


def test_zoom_buttons_stand_down_until_the_canvas_registers():
    # Arrange
    canvas_pane = (
        _FRONTEND / "components" / "CanvasPane" / "CanvasPane.tsx"
    ).read_text(encoding="utf-8")
    details = _PROPS.read_text(encoding="utf-8")
    # Act: Fit stands down when THIS canvas has no figures (1 Figure =
    # 1 Canvas: the guard reads the canvas-filtered list, not the global
    # placed list, so an empty canvas never offers a fit into nothing).
    problems = [
        check
        for check, present in [
            (
                "Figure-tab Fit clickable with no controls",
                "canvasFigures.length === 0 || !zoomControls" in canvas_pane,
            ),
            (
                "Details Zoom clickable with no controls",
                details.count("disabled={!zoomControls}") >= 4,
            ),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_rulers_toggle_collapses_the_ruler_tracks():
    # Arrange
    canvas = (
        _FRONTEND / "components" / "Canvas" / "Canvas.tsx"
    ).read_text(encoding="utf-8")
    css = (_FRONTEND / "styles" / "canvas.css").read_text(encoding="utf-8")
    # Act
    problems = [
        check
        for check, present in [
            ("Canvas never reads showRulers", "showRulers" in canvas),
            (
                "no collapsed-rulers class",
                "rulers-hidden" in canvas and ".vis-rulers-area.rulers-hidden" in css,
            ),
            (
                "hidden rulers keep dead gutters",
                'grid-template-areas: "canvas"' in css,
            ),
        ]
        if not present
    ]
    # Assert
    assert problems == []
