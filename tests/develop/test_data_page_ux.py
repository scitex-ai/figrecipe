#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SigmaPlot-style Data page, guided empty states, labeled actions.

Owner verdict 2026-09-27: the GUI opened on an empty grid with 'No tables'
and no Import CTA, a black viewer, a Details pane saying 'select from the
tree' with no tree visible, tiny unlabeled icons, and a dock covering rows.
The remodel: data entry lives on its own full-width Data page (not squeezed
beside the viewer), the Objects tree is always visible above Details, every
empty state names the way in, toolbar actions carry text labels, and the
desktop layout reserves the Hub dock height.

Source-conformance gates: a missing rule fails silently and only shows up as
a dead screen, so each property below is pinned to the exact source that
renders it. Each test makes a single assertion.
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
_STYLES = _FRONTEND / "styles"
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


def test_data_tab_renders_the_table_full_width():
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    # Act
    problems = [
        check
        for check, present in [
            ("no Data tab button", 'setActiveTab("data")' in source),
            ("no Data tab content", 'activeTab === "data"' in source),
            (
                "Data tab table is not full-page",
                "<DataTablePane hideCollapse" in source,
            ),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_plot_tab_has_no_squeezed_data_pane():
    # Arrange
    source = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    # Act
    uses = len(re.findall(r"<DataTablePane\b", source))
    # Assert
    assert (
        uses == 1
    ), f"DataTablePane must live only on the Data page, found {uses} uses"


def test_objects_tree_is_wired_above_details():
    # Arrange
    editor = (_FRONTEND / "InnerEditor.tsx").read_text(encoding="utf-8")
    pane = (
        _FRONTEND / "components" / "PropertiesPane" / "PropertiesPane.tsx"
    ).read_text(encoding="utf-8")
    tree = (_FRONTEND / "components" / "ObjectTree" / "ObjectTree.tsx").read_text(
        encoding="utf-8"
    )
    # Act
    problems = [
        check
        for check, present in [
            ("Details does not render the tree", "<ObjectTree" in pane),
            ("tree never selects a figure", "selectFigure" in tree),
            ("tree empty state has no way in", "onRequestDataTab" in tree),
            ("Plot tab cannot jump to Data", "onRequestDataTab" in editor),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_data_empty_state_names_all_three_ways_in():
    # Arrange
    source = (
        _FRONTEND / "components" / "DataTablePane" / "DataTablePane.tsx"
    ).read_text(encoding="utf-8")
    # Act
    problems = [
        check
        for check, present in [
            ("no Import CTA", 'gettext("Import CSV")' in source),
            ("no Paste CTA", 'gettext("Paste data")' in source),
            ("no Sample CTA", 'gettext("Load sample data")' in source),
            (
                "starter grid still renders with no tables",
                "tabs.length === 0 ?" in source,
            ),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_viewer_names_loading_instead_of_going_black():
    # Arrange
    source = (_FRONTEND / "components" / "FigureViewer" / "FigureViewer.tsx").read_text(
        encoding="utf-8"
    )
    # Act
    problems = [
        check
        for check, present in [
            ("no loading branch", "if (!previewImage)" in source),
            ("loading branch has no words", 'gettext("Preparing a figure…")' in source),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_desktop_layout_reserves_the_hub_dock():
    # Arrange
    css = (_STYLES / "layout.css").read_text(encoding="utf-8")
    # Act
    bodies = [
        body
        for selectors, body in re.findall(r"([^{}]+)\{([^}]*)\}", css)
        if ".editor-body" in [s.strip() for s in selectors.split(",")]
    ]
    # Assert
    assert any(
        "var(--site-dock-height, 0px)" in body for body in bodies
    ), f".editor-body must reserve var(--site-dock-height, 0px); found: {bodies}"


def test_pane_actions_carry_visible_text_labels():
    # Arrange
    data = (_FRONTEND / "components" / "DataTablePane" / "DataTablePane.tsx").read_text(
        encoding="utf-8"
    )
    canvas = (_FRONTEND / "components" / "CanvasPane" / "CanvasPane.tsx").read_text(
        encoding="utf-8"
    )
    layout = (_STYLES / "layout.css").read_text(encoding="utf-8")
    # Act
    problems = [
        check
        for check, present in [
            ("Data pane has icon-only buttons", "pane-header-btn__label" in data),
            ("Canvas pane has icon-only buttons", "pane-header-btn__label" in canvas),
            ("no label style", ".pane-header-btn__label" in layout),
        ]
        if not present
    ]
    # Assert
    assert problems == []


def test_plot_rail_uses_full_category_names():
    # Arrange
    source = (_FRONTEND / "components" / "PlotTypeNav" / "PlotTypeNav.tsx").read_text(
        encoding="utf-8"
    )
    # Act
    problems = []
    if 'gettext_noop("Distribution")' not in source:
        problems.append("rail still abbreviates Distribution")
    if 'gettext_noop("Statistics")' not in source:
        problems.append("rail still abbreviates Statistics")
    if re.search(r'gettext_noop\("(Dist|Stats)"\)', source):
        problems.append("abbreviated rail labels remain")
    # Assert
    assert problems == []


def test_new_strings_ship_with_japanese():
    # Arrange
    catalog = _LOCALE.read_text(encoding="utf-8")
    # Act
    wanted = [
        "Data table — its own full-width page",
        "Objects",
        "No figures yet.",
        "Go to Data",
        "Paste data",
        "Load sample data",
        "Sample data loaded",
        "Regions",
        "Sort",
        "Filter",
        "Nothing open yet? Pick a figure in Objects above, or enter data on the Data page.",
    ]
    missing = [
        label
        for label in wanted
        if f'msgid "{label}"\nmsgstr ""' in catalog or f'msgid "{label}"' not in catalog
    ]
    # Assert
    assert missing == []


def test_sample_import_bootstraps_recipe_on_fresh_session():
    # Arrange
    source = (
        _FRONTEND / "components" / "DataTablePane" / "DataTablePane.tsx"
    ).read_text(encoding="utf-8")
    # Act: the import path retries once after api/new when no recipe is loaded.
    has_retry = "api/new" in source and "No recipe loaded" in source
    # Assert
    assert has_retry
