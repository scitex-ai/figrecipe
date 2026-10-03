"""Native regressions for the editor view's shipped pane/gesture assets with real shipped assets and synthetic HTTP.

The fixture supplies only the documented app-content/file-tree slots. It does
not run an engine, database, real project, full SDK shell, or deployed server.
"""

import base64
import csv
import gettext
import io
import json
import os
import struct
import threading
import urllib.parse
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ASSETS = REPO / "src/figrecipe/_django/static/figrecipe"
LOCALE = REPO / "src/figrecipe/_django/locale/ja/LC_MESSAGES/djangojs.mo"


def _image():
    width, height = 320, 240
    rows = b"".join(b"\0" + bytes([235, 235, 235]) * width for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    return base64.b64encode(png).decode()


@pytest.fixture
def editor_server():
    table = {"columns": [{"name": "time", "dtype": "float64"}, {"name": "signal", "dtype": "float64"}], "rows": [[row, row * 2] for row in range(80)]}
    preview = {"image": _image(), "bboxes": {}, "img_size": {"width": 320, "height": 240}, "dark_mode": True}
    with LOCALE.open("rb") as stream:
        catalog = gettext.GNUTranslations(stream)
    ja = {"language": "ja", "plural": "0", "catalog": {key: value for key, value in catalog._catalog.items() if isinstance(key, str) and key}}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send(self, payload, mime="application/json", status=200):
            content = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            if path == "/":
                language = "ja" if "lang=ja" in self.path else "en"
                translations = '<script type="application/json" id="scitex-i18n-catalog-test">' + json.dumps(ja, ensure_ascii=False) + '</script>' if language == "ja" else ""
                html = '<!doctype html><html lang="' + language + '"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/static/figrecipe/assets/index.css">' + translations + '<style>html,body,#root{height:100%;margin:0;overflow:hidden}</style></head><body data-api-base=""><aside id="ws-worktree-tree" style="display:none"></aside><div id="root" data-version="0.36.0" data-working-dir="/synthetic" data-hosted="false"></div><script type="module" src="/static/figrecipe/assets/index.js"></script></body></html>'
                if "fixture=workspace" in self.path:
                    mount = '<div id="app-mount" data-app-slug="figrecipe" data-embedded="true" data-stx-mount="" data-recipe="synthetic.yaml" data-working-dir="/synthetic"></div>'
                    html = '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/static/figrecipe/assets/index.css"><style>html,body,#app-mount{height:100%;margin:0;overflow:hidden}</style></head><body>' + mount + '<script type="module" src="/static/figrecipe/assets/workspace.js"></script></body></html>'
                self.send(html.encode(), "text/html")
            elif path.startswith("/static/figrecipe/"):
                file = ASSETS / path.removeprefix("/static/figrecipe/")
                if file.is_file() and file.resolve().is_relative_to(ASSETS.resolve()):
                    self.send(file.read_bytes(), "text/javascript" if file.suffix == ".js" else "text/css")
                else:
                    self.send({}, status=404)
            elif path in ("/api/files", "/api/tree"):
                self.send({"tree": [{"name": "synthetic.yaml", "path": "synthetic.yaml", "type": "file", "is_current": True, "has_image": True}], "files": [], "current_file": "synthetic.yaml", "working_dir": "/synthetic"})
            elif path == "/preview":
                self.send(preview)
            elif path == "/hitmap":
                self.send({"image": preview["image"], "color_map": {}})
            elif path == "/datatable/data":
                self.send(table)
            elif path == "/list_themes":
                self.send({"themes": ["dark"], "current": "dark"})
            elif path == "/get_axes_positions":
                self.send({"_figsize": {"width_mm": 100, "height_mm": 75}})
            elif path == "/calls":
                self.send({"calls": []})
            elif path == "/api/gallery":
                self.send({"categories": {}})
            else:
                self.send({})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
            if self.path.startswith("/datatable/import"):
                rows = list(csv.reader(io.StringIO(body["content"])))
                table.update({"columns": [{"name": name, "dtype": "float64"} for name in rows[0]], "rows": rows[1:]})
            self.send({"success": True})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:" + str(server.server_port), ja["catalog"]
    server.shutdown()
    server.server_close()


@pytest.fixture
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        executable = Path(os.environ.get("FIGRECIPE_TEST_CHROMIUM", runtime.chromium.executable_path))
        if not executable.is_file():
            pytest.skip("Chromium is not installed")
        instance = runtime.chromium.launch(executable_path=str(executable), headless=True, args=["--no-sandbox"])
        yield instance
        instance.close()


def _settle(page):
    page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")


def _touch(page, start, moves):
    session = page.context.new_cdp_session(page)
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": start})
    for points in moves:
        session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": points})
        _settle(page)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    _settle(page)
    session.detach()


@pytest.mark.parametrize("language", ["en", "ja"])
def test_phone_workflow_keeps_panes_and_canvas_view(browser, editor_server, language):
    # Arrange
    url, catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url + "/?recipe=synthetic.yaml&mode=embedded&lang=" + language, wait_until="networkidle")
    page.evaluate("window.paneRefs=Array.from(document.querySelectorAll('.editor-body > [data-stx-pane]'))")

    # Act
    for pane in ["data", "plot", "figure", "details", "data", "figure"]:
        page.locator('.stx-panes__tab[data-stx-pane-tab="' + pane + '"]').tap()
        _settle(page)
    surface = page.locator(".canvas-outer")
    rect = surface.bounding_box()
    anchor = surface.evaluate("""e => {const r=e.getBoundingClientRect();for(let y=Math.min(r.bottom-100,innerHeight-100);y>r.top+30;y-=30){for(let x=r.left+40;x<r.right-60;x+=30){const t=document.elementFromPoint(x,y);if(t && e.contains(t) && !t.closest('.placed-figure,.context-menu,button,input'))return {x,y};}}throw Error('No visible unoccupied canvas');}""")
    before = page.locator(".vis-rulers-area").evaluate("e=>getComputedStyle(e).transform")
    _touch(page, [{"id": 1, "x": anchor["x"], "y": anchor["y"]}], [[{"id": 1, "x": anchor["x"] + step * 12, "y": anchor["y"] + step * 10}] for step in range(1, 6)])
    after = page.locator(".vis-rulers-area").evaluate("e=>getComputedStyle(e).transform")
    page.locator('.stx-panes__tab[data-stx-pane-tab="plot"]').tap()
    page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').tap()
    _settle(page)
    labels = page.locator(".stx-panes__tab").all_text_contents()
    expected = [catalog.get(label, label) if language == "ja" else label for label in ["Data", "Plot", "Figure", "Details"]]

    # Assert
    checks = {
        "labels": labels == expected,
        "one_visible_tablist": page.locator('.inner-editor [role="tablist"]:visible').count() == 1,
        "stable_panes": page.evaluate("window.paneRefs.length===4 && window.paneRefs.every(e=>e.isConnected && document.getElementById(e.id)===e)"),
        "plot_navigation": page.locator(".editor-plot-page .plot-type-nav").count() == 1,
        "plot_viewer": page.locator(".editor-plot-page .figure-viewer").count() == 1,
        "one_canvas": page.locator(".canvas-outer").count() == 1,
        "viewport": rect["y"] + rect["height"] <= 844,
        "canvas_touch": surface.evaluate("e=>getComputedStyle(e).touchAction") == "none",
        "native_pan": before != after,
        "retained_view": page.locator(".vis-rulers-area").evaluate("e=>getComputedStyle(e).transform") == after,
        "no_raw_comment": "/*" not in page.locator(".inner-editor").inner_text(),
        "no_errors": not errors,
    }
    assert all(checks.values()), checks
    context.close()


def test_hidden_worksheet_does_not_intercept_canvas_undo(browser, editor_server):
    # Arrange
    url, _catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = context.new_page()
    page.goto(url + "/?recipe=synthetic.yaml&mode=embedded", wait_until="networkidle")
    page.evaluate("window.lastDataContext=false;document.addEventListener('mousedown',e=>window.lastDataContext=!!e.target.closest('.data-page'),true)")
    original_rows = page.locator("tbody tr").count()
    page.get_by_role("button", name="Add row", exact=True).tap()
    page.wait_for_function("n => document.querySelectorAll('tbody tr').length===n", arg=original_rows + 1)
    page.wait_for_load_state("networkidle")
    rows = page.locator("tbody tr").count()

    # Act
    page.locator(".plot-from-columns").get_by_role("button", name="Plot", exact=True).tap()
    page.wait_for_function("document.querySelector('.stx-panes__tab[data-stx-pane-tab=figure]').getAttribute('aria-selected')==='true'")
    data_context = page.evaluate("window.lastDataContext")
    page.keyboard.press("Control+z")
    _settle(page)

    # Assert
    checks = {"data_context": data_context, "unchanged_rows": page.locator("tbody tr").count() == rows, "figure_visible": page.locator(".editor-figure-page").is_visible()}
    assert all(checks.values()), checks
    context.close()


@pytest.mark.parametrize("saved,expected", [({}, "data"), ({"figrecipe-app-tab": "canvas"}, "figure"), ({"figrecipe-app-tab": "plot"}, "plot"), ({"figrecipe-app-tab": "unknown"}, "data")])
def test_phone_initial_pane_respects_legacy_canvas_token(browser, editor_server, saved, expected):
    # Arrange
    url, _catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    context.add_init_script("Object.entries(" + json.dumps(saved) + ").forEach(([k,v])=>localStorage.setItem(k,v))")
    page = context.new_page()
    page.goto(url + "/?recipe=synthetic.yaml&mode=embedded", wait_until="networkidle")
    initial = page.locator('.stx-panes__tab[aria-selected="true"]').get_attribute("data-stx-pane-tab")
    initial_canvas_count = page.locator(".canvas-outer").count()

    # Act
    page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').tap()
    _settle(page)
    surface = page.locator(".canvas-outer").bounding_box()

    # Assert
    checks = {"initial": initial == expected, "lazy_hidden_canvas": initial_canvas_count == (1 if expected == "figure" else 0), "one_canvas": page.locator(".canvas-outer").count() == 1, "visible_fit_viewport": surface["width"] > 0 and surface["height"] > 200}
    assert all(checks.values()), checks
    context.close()


def test_worksheet_native_scroll_does_not_pan_hidden_canvas(browser, editor_server):
    # Arrange
    url, _catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = context.new_page()
    page.goto(url + "/?recipe=synthetic.yaml&mode=embedded", wait_until="networkidle")
    page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').tap()
    _settle(page)
    page.locator('.stx-panes__tab[data-stx-pane-tab="data"]').tap()
    _settle(page)
    canvas_before = page.locator(".vis-rulers-area").evaluate("e=>getComputedStyle(e).transform")
    scroll = page.locator(".stx-app-data-table__scroll")
    rect = scroll.bounding_box()
    before = scroll.evaluate("e=>e.scrollTop")
    y = min(rect["y"] + rect["height"] - 60, 784)

    # Act
    _touch(page, [{"id": 1, "x": 20, "y": y}], [[{"id": 1, "x": 20, "y": y - step * 30}] for step in range(1, 7)])
    after = scroll.evaluate("e=>e.scrollTop")

    # Assert
    checks = {"native_scroll": after > before + 50, "outside_touch_auto": scroll.evaluate("e=>getComputedStyle(e).touchAction") == "auto", "canvas_unchanged": page.locator(".vis-rulers-area").evaluate("e=>getComputedStyle(e).transform") == canvas_before, "data_remains_active": page.locator('.stx-panes__tab[data-stx-pane-tab="data"]').get_attribute("aria-selected") == "true"}
    assert all(checks.values()), checks
    context.close()


def test_workspace_remount_routes_named_plot_to_live_editor(browser, editor_server):
    # Arrange
    url, _catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url + "/?fixture=workspace", wait_until="networkidle")
    page.locator('.stx-panes__tab[data-stx-pane-tab="data"]').tap()
    page.locator(".plot-from-columns").get_by_role("button", name="Plot", exact=True).tap()
    page.wait_for_function("document.querySelector('.stx-panes__tab[data-stx-pane-tab=figure]').getAttribute('aria-selected')==='true'")

    # Act
    page.evaluate("() => {window.oldEditor=document.querySelector('.editor-body');const old=document.getElementById('app-mount');old.replaceWith(old.cloneNode(false));document.dispatchEvent(new CustomEvent('workspace:module-injected'));}")
    page.locator(".stx-panes__tabs").wait_for()
    page.wait_for_load_state("networkidle")
    page.locator('.stx-panes__tab[data-stx-pane-tab="data"]').tap()
    page.locator(".plot-from-columns").get_by_role("button", name="Plot", exact=True).tap()
    page.wait_for_load_state("networkidle")
    _settle(page)

    # Assert
    checks = {"old_detached": page.evaluate("!window.oldEditor.isConnected"), "one_live_root": page.locator(".editor-body").count() == 1, "one_tablist": page.locator(".stx-panes__tabs").count() == 1, "current_figure": page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').get_attribute("aria-selected") == "true", "no_errors": not errors}
    assert all(checks.values()), checks
    context.close()


@pytest.mark.parametrize("start,target", [("data", "plot"), ("plot", "figure")])
def test_native_tab_arrows_preserve_geometry_and_canvas_arrows_edit(browser, editor_server, start, target):
    # Arrange
    url, _catalog = editor_server
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = context.new_page()
    page.goto(url + "/?recipe=synthetic.yaml&mode=embedded", wait_until="networkidle")
    page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').tap()
    figure = page.locator(".placed-figure").first
    figure.wait_for()
    tab = page.locator('.stx-panes__tab[data-stx-pane-tab="' + start + '"]')
    tab.tap()
    before = figure.evaluate("e=>({left:e.style.left,top:e.style.top})")

    # Act
    tab.focus()
    page.keyboard.press("ArrowRight")
    _settle(page)
    tab_geometry = figure.evaluate("e=>({left:e.style.left,top:e.style.top})")
    tab_active = page.locator('.stx-panes__tab[aria-selected="true"]').get_attribute("data-stx-pane-tab")
    page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').tap()
    figure.click()
    page.keyboard.press("ArrowRight")
    _settle(page)
    canvas_geometry = figure.evaluate("e=>({left:e.style.left,top:e.style.top})")

    # Assert
    checks = {"tab_navigation": tab_active == target, "tab_does_not_edit": tab_geometry == before, "canvas_still_edits": canvas_geometry["left"] != tab_geometry["left"] and canvas_geometry["top"] == tab_geometry["top"], "figure_remains_active": page.locator('.stx-panes__tab[data-stx-pane-tab="figure"]').get_attribute("aria-selected") == "true"}
    assert all(checks.values()), checks
    context.close()
