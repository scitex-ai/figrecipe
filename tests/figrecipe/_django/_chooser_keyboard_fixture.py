"""Native chooser-key regressions against shipping assets and synthetic HTTP.

Reuse the mobile workflow's actual browser and server. Only gallery HTTP is
adapted through browser route fulfillment: public literal metadata, packaged
thumbnails and existing translations describe the inputs. Browser-originated
add/switch requests receive synthetic replies without reaching those handlers,
copying files, running an engine or accessing a database.
Every focus change comes from normal keyboard input or a native select tap.
"""

import ast
import base64
import gettext
import importlib.util
import json
import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "native_mobile_workflow", Path(__file__).with_name("test_views_mobile_workflow.py")
)
_MOBILE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOBILE)
browser = _MOBILE.browser
editor_server = _MOBILE.editor_server
REPO = _MOBILE.REPO


def _gallery_inputs(language):
    tree = ast.parse((REPO / "src/figrecipe/_django/handlers/gallery.py").read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "GALLERY_TEMPLATES"
            for target in node.targets
        )
    )

    class LiteralLabels(ast.NodeTransformer):
        def visit_Call(self, node):
            if (
                not isinstance(node.func, ast.Name)
                or node.func.id != "gettext_noop"
                or len(node.args) != 1
                or node.keywords
            ):
                raise ValueError("Gallery fixture requires literal public labels")
            return node.args[0]

    metadata = ast.literal_eval(LiteralLabels().visit(assignment.value))
    with (REPO / "src/figrecipe/_django/locale/ja/LC_MESSAGES/django.mo").open(
        "rb"
    ) as stream:
        translations = gettext.GNUTranslations(stream)
    categories, images = {}, {}
    for family in ("line", "special"):
        categories[family] = []
        for template in metadata[family]:
            name = template["name"]
            recipe = REPO / "src/figrecipe/_django/gallery_templates" / (name + ".yaml")
            label = template["label"]
            if language == "ja":
                label = translations.gettext(label)
            categories[family].append(
                dict(template, label=label, path=str(recipe), has_thumbnail=True)
            )
            images[name] = "data:image/png;base64," + base64.b64encode(
                recipe.with_suffix(".png").read_bytes()
            ).decode("ascii")
    return categories, images


@dataclass
class ChooserCase:
    page: object
    phone: bool
    language: str
    catalog: dict
    categories: dict
    posts: list
    errors: list
    http_errors: list
    requests: list
    artifact_dir: Path | None = None

    def label(self, text):
        return self.catalog.get(text, text) if self.language == "ja" else text

    def template_label(self, name):
        return next(
            template["label"]
            for template in self.categories["special"]
            if template["name"] == name
        )


@pytest.fixture
def chooser(browser, editor_server, view, request):
    phone, language = view
    url, catalog = editor_server
    categories, images = _gallery_inputs(language)
    context = browser.new_context(
        viewport={"width": 390 if phone else 1440, "height": 844 if phone else 1000},
        has_touch=phone,
        is_mobile=phone,
        locale="ja-JP" if language == "ja" else "en-US",
    )
    page = context.new_page()
    page.set_default_timeout(7000)
    evidence = os.environ.get("FIGRECIPE_CHOOSER_EVIDENCE_DIR")
    directory = (
        Path(evidence) / urllib.parse.quote(request.node.name, safe="._-")
        if evidence
        else None
    )
    case = ChooserCase(
        page, phone, language, catalog, categories, [], [], [], [], directory
    )

    def gallery_response(route):
        path = urllib.parse.urlsplit(route.request.url).path
        if path == "/api/gallery":
            payload = {"categories": categories}
        elif path.startswith("/api/gallery/thumbnail/"):
            payload = {"image": images[path.rsplit("/", 1)[-1]]}
        elif path == "/api/gallery/add":
            name = route.request.post_data_json.get("template")
            if name not in images:
                route.fulfill(
                    status=400, json={"error": "Unknown public fixture template"}
                )
                return
            payload = {"recipe_path": name + ".yaml"}
        else:
            route.continue_()
            return
        route.fulfill(json=payload)

    def switch_response(route):
        # Preserve the original synthetic preview, adding only the public switch field.
        preview = page.request.get(url + "/preview").json()
        route.fulfill(json=dict(preview, working_dir="/synthetic"))

    page.route("**/api/gallery**", gallery_response)
    page.route("**/api/switch**", switch_response)

    def record_request(request):
        path = urllib.parse.urlsplit(request.url).path
        body = request.post_data_json if request.method == "POST" else None
        case.requests.append({"method": request.method, "path": path, "body": body})
        if request.method == "POST":
            case.posts.append((path, body))

    page.on("request", record_request)
    page.on("pageerror", lambda error: case.errors.append(str(error)))
    page.on(
        "console",
        lambda message: case.errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on(
        "response",
        lambda response: case.http_errors.append((response.status, response.url))
        if response.status >= 400
        else None,
    )
    try:
        page.goto(
            url + "/?recipe=synthetic.yaml&mode=embedded&lang=" + language,
            wait_until="networkidle",
        )
        yield case
    finally:
        try:
            capture(case, "final")
        finally:
            context.close()


def capture(case, step):
    """Optional real screenshots and read-only focus/request observations."""
    if case.artifact_dir is None:
        return
    case.artifact_dir.mkdir(parents=True, exist_ok=True)
    page = case.page
    observed = page.evaluate("""() => {
        const e = document.activeElement;
        const describe = n => n ? {tag: n.tagName, text: n.textContent.trim().slice(0, 160),
            class: n.className, value: n.value, tabIndex: n.tabIndex} : null;
        return {focus: describe(e), pane: document.querySelector('.inner-editor')?.dataset.editorTab,
            sdkPane: document.querySelector('.stx-panes__tab[aria-selected=true]')?.dataset.stxPaneTab,
            recipe: new URL(location.href).searchParams.get('recipe'),
            activeVariant: describe(document.querySelector('.plot-type-nav__chooser .is-active')),
            figures: Array.from(document.querySelectorAll('.placed-figure')).map(n =>
                ({path: n.querySelector('.canvas-image')?.alt, left: n.style.left,
                  top: n.style.top, selected: n.classList.contains('selected')}))};
    }""")
    page.screenshot(path=str(case.artifact_dir / (step + ".png")), full_page=True)
    (case.artifact_dir / (step + ".json")).write_text(
        json.dumps(
            {
                "view": {"phone": case.phone, "language": case.language},
                "observed": observed,
                "requests": case.requests,
                "page_console_errors": case.errors,
                "http_errors": case.http_errors,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
