"""Native chooser keyboard contracts using real shipping DOM and fixture HTTP."""

import importlib.util
import urllib.parse
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "chooser_keyboard_fixture", Path(__file__).with_name("_chooser_keyboard_fixture.py")
)
_ADAPTER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ADAPTER)
browser = _ADAPTER.browser
editor_server = _ADAPTER.editor_server
chooser_session = _ADAPTER.chooser
_MOBILE = _ADAPTER._MOBILE
_capture = _ADAPTER.capture
CHOOSER = ".plot-type-nav__chooser"
VARIANT = (
    CHOOSER + " .plot-type-nav__chooser-item:not(.plot-type-nav__chooser-item--data)"
)
DATA_ACTION = CHOOSER + " .plot-type-nav__chooser-item--data"
VIEWS = [(False, "en"), (True, "en"), (True, "ja")]
VIEW_IDS = ["desktop-en", "phone390-en", "phone390-ja"]


@pytest.fixture
def chooser(chooser_session):
    _to_plot(chooser_session)
    return chooser_session


def _settle(page):
    _MOBILE._settle(page)


def _focused(locator):
    return locator.count() == 1 and locator.evaluate(
        "e => e === document.activeElement"
    )


def _tab_to(page, locator, backward=False):
    for _ in range(80):
        if _focused(locator):
            return
        page.keyboard.press("Shift+Tab" if backward else "Tab")
        _settle(page)
    raise RuntimeError("Normal Tab did not reach " + str(locator))


def _rail(case, family):
    return case.page.locator(".editor-plot-page .plot-type-nav").get_by_role(
        "button",
        name=case.label("Special" if family == "special" else "Line"),
        exact=True,
    )


def _to_plot(case):
    page = case.page
    if page.locator(".editor-plot-page").is_visible():
        return
    if case.phone:
        # SDK tabs have one roving tab stop; use its native arrows to reach Plot.
        active = page.locator('.stx-panes__tab[aria-selected="true"]')
        _tab_to(page, active)
        current = active.get_attribute("data-stx-pane-tab")
        for key in {
            "data": ["ArrowRight"],
            "figure": ["ArrowLeft"],
            "details": ["ArrowLeft", "ArrowLeft"],
        }[current]:
            page.keyboard.press(key)
            _settle(page)
    else:
        tab = page.locator(".inner-editor__tabs").get_by_role(
            "tab", name="Plot", exact=True
        )
        _tab_to(page, tab)
        page.keyboard.press("Enter")
    page.locator(".editor-plot-page").wait_for(state="visible")
    _settle(page)


def _wait_variant_focus(case, name):
    case.page.wait_for_function(
        """label => {const e = document.activeElement;
        return !!e && e.matches('.plot-type-nav__chooser-item:not(.plot-type-nav__chooser-item--data)')
            && e.textContent.trim() === label;}""",
        arg=case.template_label(name),
    )


def _open_special(case):
    _tab_to(case.page, _rail(case, "special"))
    case.page.keyboard.press("ArrowDown")
    case.page.locator(CHOOSER).wait_for(state="visible")
    _wait_variant_focus(case, "plot_pie")
    _capture(case, "special-open")


def _select_special_family(case):
    _tab_to(case.page, _rail(case, "special"))
    case.page.keyboard.press("Enter")
    surface = CHOOSER if case.phone else ".gallery-panel"
    case.page.locator(surface).wait_for(state="visible")
    if case.phone:
        case.page.keyboard.press("Escape")
    else:
        _tab_to(case.page, case.page.locator(".gallery-close"))
        case.page.keyboard.press("Enter")
    case.page.locator(surface).wait_for(state="hidden")
    _settle(case.page)


def _choose_specgram(case, select_family=False):
    if select_family:
        _select_special_family(case)
    _open_special(case)
    case.page.keyboard.press("ArrowDown")
    _wait_variant_focus(case, "plot_specgram")
    with case.page.expect_response(
        lambda response: response.request.method == "POST"
        and urllib.parse.urlsplit(response.url).path == "/api/gallery/add"
    ):
        with case.page.expect_response(
            lambda response: response.request.method == "POST"
            and urllib.parse.urlsplit(response.url).path == "/api/switch"
        ):
            case.page.keyboard.press("Enter")
    case.page.locator(".editor-figure-page").wait_for(state="visible")
    case.page.locator(
        '.placed-figure.selected .canvas-image[alt="plot_specgram.yaml"]'
    ).wait_for()
    case.page.wait_for_load_state("networkidle")
    _settle(case.page)


def _figures(page):
    return page.locator(".placed-figure").evaluate_all(
        """figures => figures.map(e => ({path: e.querySelector('.canvas-image')?.alt,
        left: e.style.left, top: e.style.top, selected: e.classList.contains('selected')}))"""
    )


def _pane(page):
    return page.locator(".inner-editor").get_attribute("data-editor-tab")


def _data_from_line(case, activation="Enter"):
    _to_plot(case)
    _tab_to(case.page, _rail(case, "line"))
    case.page.keyboard.press("ArrowDown")
    case.page.locator(CHOOSER).wait_for(state="visible")
    case.page.wait_for_function(
        "document.activeElement?.matches('.plot-type-nav__chooser-item:not(.plot-type-nav__chooser-item--data)')"
    )
    action = case.page.locator(DATA_ACTION)
    _tab_to(case.page, action, backward=True)
    before = _figures(case.page)
    posts = len(case.posts)
    _capture(case, "line-data-focus")
    case.page.keyboard.press("ArrowRight")
    _settle(case.page)
    arrow = {
        "focus": _focused(action),
        "figures": _figures(case.page) == before,
        "no_posts": len(case.posts) == posts,
    }
    _capture(case, "line-data-arrow")
    case.page.keyboard.press(activation)
    case.page.locator(".data-page").wait_for(state="visible")
    case.page.wait_for_load_state("networkidle")
    _settle(case.page)
    _capture(case, "line-data-result")
    return arrow, posts


def _prepare_utility(case, control):
    page = case.page
    _choose_specgram(case, select_family=True)
    _to_plot(case)
    _open_special(case)
    page.keyboard.press("ArrowDown")
    _wait_variant_focus(case, "plot_specgram")
    utility = page.locator(CHOOSER + " .plot-type-nav__chooser-" + control)
    _tab_to(page, utility, backward=control == "close")
    before, posts = _figures(page), len(case.posts)
    _capture(case, "utility-focus")
    return utility, before, posts


def _activate_utility(case, utility, activation, before, posts):
    page = case.page
    page.keyboard.press("ArrowRight")
    _settle(page)
    observed = {
        "utility_keeps_focus": _focused(utility),
        "arrow_keeps_figures": _figures(page) == before,
        "arrow_sends_no_post": len(case.posts) == posts,
    }
    _capture(case, "utility-arrow")
    page.keyboard.press(activation)
    page.locator(CHOOSER).wait_for(state="hidden")
    return observed


def _utility_result(case, observed, before, posts, focused):
    page = case.page
    page.wait_for_load_state("networkidle")
    _settle(page)
    observed.update(
        {
            "plot_visible": page.locator(".editor-plot-page").is_visible(),
            "pane": _pane(page),
            "focus": focused,
            "gallery": page.locator(".gallery-panel").is_visible(),
            "gallery_labels": page.locator(
                ".gallery-panel .gallery-item-label"
            ).all_text_contents(),
            "unchanged_figures": _figures(page) == before,
            "no_posts": len(case.posts) == posts,
            "errors": case.errors,
            "http_errors": case.http_errors,
        }
    )
    _capture(case, "utility-result")
    return observed


@pytest.mark.parametrize("view", VIEWS, ids=VIEW_IDS)
@pytest.mark.parametrize("activation", ["Enter", "Space"])
def test_chooser_utility_close_preserves_hidden_figures(chooser, activation):
    # Arrange
    case, page = chooser, chooser.page
    utility, before, posts = _prepare_utility(case, "close")

    # Act
    observed = _activate_utility(case, utility, activation, before, posts)
    page.wait_for_function(
        "label => document.activeElement?.matches('.stx-app-selector-nav__item') && document.activeElement.textContent.trim() === label",
        arg=case.label("Special"),
    )
    observed = _utility_result(
        case, observed, before, posts, _focused(_rail(case, "special"))
    )

    # Assert
    assert observed == {
        "utility_keeps_focus": True,
        "arrow_keeps_figures": True,
        "arrow_sends_no_post": True,
        "plot_visible": True,
        "pane": "plot",
        "focus": True,
        "gallery": False,
        "gallery_labels": [],
        "unchanged_figures": True,
        "no_posts": True,
        "errors": [],
        "http_errors": [],
    }


@pytest.mark.parametrize("view", VIEWS, ids=VIEW_IDS)
@pytest.mark.parametrize("activation", ["Enter", "Space"])
def test_chooser_utility_see_all_preserves_hidden_figures(chooser, activation):
    # Arrange
    case, page = chooser, chooser.page
    utility, before, posts = _prepare_utility(case, "more")

    # Act
    observed = _activate_utility(case, utility, activation, before, posts)
    page.locator(".gallery-panel").wait_for(state="visible")
    _tab_to(page, page.locator(".gallery-close"))
    observed = _utility_result(
        case, observed, before, posts, _focused(page.locator(".gallery-close"))
    )

    # Assert
    assert observed == {
        "utility_keeps_focus": True,
        "arrow_keeps_figures": True,
        "arrow_sends_no_post": True,
        "plot_visible": True,
        "pane": "plot",
        "focus": True,
        "gallery": True,
        "gallery_labels": [t["label"] for t in case.categories["special"]],
        "unchanged_figures": True,
        "no_posts": True,
        "errors": [],
        "http_errors": [],
    }


@pytest.mark.parametrize("view", VIEWS, ids=VIEW_IDS)
@pytest.mark.parametrize("activation", ["Enter", "Space"])
def test_keyboard_line_data_route_replaces_selected_special_family(chooser, activation):
    # Arrange
    case, page = chooser, chooser.page
    _choose_specgram(case, select_family=True)

    # Act
    arrow, posts = _data_from_line(case, activation)
    select = page.locator(".plot-from-columns select").first
    select.wait_for(state="visible")
    observed = {
        "arrow": arrow,
        "pane": _pane(page),
        "data": page.locator(".data-page").is_visible(),
        "line_form": case.label("Line")
        in page.locator(".plot-from-columns").inner_text(),
        "x_value": select.input_value(),
        "x_options": select.locator("option").all_text_contents(),
        "no_posts": len(case.posts) == posts,
        "errors": case.errors,
        "http_errors": case.http_errors,
    }

    # Assert
    assert observed == {
        "arrow": {"focus": True, "figures": True, "no_posts": True},
        "pane": "data",
        "data": True,
        "line_form": True,
        "x_value": "time",
        "x_options": [case.label("Row number"), "time", "signal"],
        "no_posts": True,
        "errors": [],
        "http_errors": [],
    }


@pytest.mark.parametrize("view", VIEWS, ids=VIEW_IDS)
def test_escape_reopen_focus_can_select_fresh_specgram(chooser):
    # Arrange
    case, page = chooser, chooser.page
    _open_special(case)
    posts = len(case.posts)

    # Act
    page.keyboard.press("ArrowDown")
    _wait_variant_focus(case, "plot_specgram")
    page.keyboard.press("Escape")
    page.locator(CHOOSER).wait_for(state="hidden")
    restored = _focused(_rail(case, "special"))
    escaped_without_post = len(case.posts) == posts
    _capture(case, "escape-restored")
    page.keyboard.press("ArrowRight")
    page.locator(CHOOSER).wait_for(state="visible")
    _wait_variant_focus(case, "plot_pie")
    reopened_focus = _focused(page.locator(VARIANT).first)
    _capture(case, "reopen-focused")
    page.keyboard.press("ArrowDown")
    _wait_variant_focus(case, "plot_specgram")
    page.keyboard.press("Enter")
    page.locator(".editor-figure-page").wait_for(state="visible")
    image = page.locator(
        '.placed-figure.selected .canvas-image[alt="plot_specgram.yaml"]'
    )
    image.wait_for(state="visible")
    page.wait_for_load_state("networkidle")
    observed = {
        "restored_focus": restored,
        "escape_no_post": escaped_without_post,
        "reopened_focus": reopened_focus,
        "pane": _pane(page),
        "selected_specgram": image.count() == 1,
        "recipe": urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query).get(
            "recipe"
        ),
        "sdk_pane": page.locator('.stx-panes__tab[aria-selected="true"]').get_attribute(
            "data-stx-pane-tab"
        ),
        "add": [
            (path, body.get("template"))
            for path, body in case.posts[posts:]
            if path == "/api/gallery/add"
        ],
        "switch": [
            (path, body.get("path"))
            for path, body in case.posts[posts:]
            if path == "/api/switch"
        ],
        "chooser_closed": page.locator(CHOOSER).count() == 0,
        "errors": case.errors,
        "http_errors": case.http_errors,
    }

    # Assert
    assert observed == {
        "restored_focus": True,
        "escape_no_post": True,
        "reopened_focus": True,
        "pane": "canvas",
        "selected_specgram": True,
        "recipe": ["/synthetic/plot_specgram.yaml"],
        "sdk_pane": "figure",
        "add": [("/api/gallery/add", "plot_specgram")],
        "switch": [("/api/switch", "plot_specgram.yaml")],
        "chooser_closed": True,
        "errors": [],
        "http_errors": [],
    }


@pytest.mark.parametrize("view", VIEWS[1:], ids=VIEW_IDS[1:])
def test_phone_native_x_select_keeps_keyboard_ownership(chooser):
    """Retain the native-select positive with an explicitly unselected canvas."""
    # Arrange
    case, page = chooser, chooser.page
    _choose_specgram(case, select_family=True)
    _data_from_line(case)
    # Existing global Escape deselects a canvas even from SELECT. Establish the
    # retained positive's unselected precondition with normal body Escape first.
    body_before_select = _focused(page.locator("body"))
    page.keyboard.press("Escape")
    _settle(page)
    select = page.locator(".plot-from-columns select").first
    select.tap()
    before, posts = _figures(page), len(case.posts)
    unselected_canvas = all(not figure["selected"] for figure in before)
    transform = page.locator(".vis-rulers-area").evaluate(
        "e => getComputedStyle(e).transform"
    )
    _capture(case, "native-select-before")

    # Act
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.keyboard.press("Escape")
    _settle(page)
    _capture(case, "native-select-result")
    observed = {
        "body_before_select": body_before_select,
        "unselected_canvas": unselected_canvas,
        "focus": _focused(select),
        "value": select.input_value(),
        "pane": _pane(page),
        "data": page.locator(".data-page").is_visible(),
        "figures": _figures(page) == before,
        "transform": page.locator(".vis-rulers-area").evaluate(
            "e => getComputedStyle(e).transform"
        )
        == transform,
        "no_posts": len(case.posts) == posts,
        "chooser_closed": page.locator(CHOOSER).count() == 0,
        "errors": case.errors,
        "http_errors": case.http_errors,
    }

    # Assert
    assert observed == {
        "body_before_select": True,
        "unselected_canvas": True,
        "focus": True,
        "value": "signal",
        "pane": "data",
        "data": True,
        "figures": True,
        "transform": True,
        "no_posts": True,
        "chooser_closed": True,
        "errors": [],
        "http_errors": [],
    }
