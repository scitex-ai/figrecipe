"""Real HTTP boundary tests with SDK providers and isolated local project files."""

import base64
import io
import json
import os
import types

import django
import pytest
from django.test import Client, override_settings
from django.urls import include, path


class FixtureUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        name = request.headers.get("X-User", "")
        request.user = types.SimpleNamespace(pk=name, is_authenticated=bool(name))
        return self.get_response(request)


class ProjectProvider:
    def list_projects(self, request):
        from scitex_sdk import ui

        ids = ("alpha",) if request.user.pk == "alice" else ("beta", "alpha")
        return [ui.project_scope.ProjectEntry(id=x, name=f"Project {x}") for x in ids]

    def last_visited(self, request):
        return "alpha" if request.user.pk == "alice" else "beta"

    def remember(self, request, project_id):
        pass


class ProjectStorage:
    def __init__(self, root):
        self.root = root

    def project_path(self, project_id, request):
        return self.root / project_id

    def can_write(self, project_id, request):
        return request.headers.get("X-Read-Only") != "1"


@pytest.fixture
def hosted(tmp_path):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()
    from figrecipe._django.services import _editor_cache

    for name in ("alpha", "beta", "alpha-neighbor"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "data.txt").write_text(name)
    (tmp_path / "alpha" / "outside").symlink_to(
        tmp_path / "beta", target_is_directory=True
    )
    module = types.ModuleType("fixture_figrecipe_urls")
    module.urlpatterns = [
        path("apps/figrecipe/", include("figrecipe._django.urls")),
        path("legacy/figrecipe/", include("figrecipe._django.urls")),
    ]
    _editor_cache.clear()
    with override_settings(
        ROOT_URLCONF=module,
        ALLOWED_HOSTS=["testserver"],
        SCITEX_APP_MODE="hub",
        SCITEX_PROJECT_PROVIDER=f"{__name__}.ProjectProvider",
        SCITEX_PROJECT_STORAGE=ProjectStorage(tmp_path),
        SCITEX_PROJECT_PROVIDER_URL="/projects/",
        MIDDLEWARE=[
            f"{__name__}.FixtureUserMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
        ],
    ):
        client = Client(enforce_csrf_checks=True, HTTP_X_USER="alice")
        response = client.get("/apps/figrecipe/")
        assert response.status_code == 200, response.content[:300]
        yield client, tmp_path
    _editor_cache.clear()


def post(client, endpoint, body=None, **headers):
    return client.post(
        f"/apps/figrecipe/{endpoint}",
        data=json.dumps(body or {}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        **headers,
    )


def test_shell_declares_mount_scope_and_host_provider(hosted):
    client, _ = hosted
    html = client.get("/apps/figrecipe/").content.decode()
    assert 'name="stx-mount" content="/apps/figrecipe"' in html
    assert html.count('name="stx-app-scope"') == 1
    assert 'name="stx-project-provider"' in html
    assert 'data-hosted="true"' in html


@pytest.mark.parametrize(
    "url", ["/apps/figrecipe/", "/apps/figrecipe/ping", "/apps/figrecipe/api/tree"]
)
def test_anonymous_denied_before_file_io(hosted, url):
    client, _ = hosted
    assert client.get(url, HTTP_X_USER="").status_code == 401


def test_explicit_other_project_does_not_fall_back(hosted):
    client, _ = hosted
    assert client.get("/apps/figrecipe/api/tree?project=beta").status_code == 404


def test_missing_provider_fails_closed(hosted):
    client, _ = hosted
    with override_settings(SCITEX_PROJECT_STORAGE=None):
        assert client.get("/apps/figrecipe/api/tree").status_code == 503
    with override_settings(SCITEX_PROJECT_PROVIDER=None):
        assert client.get("/apps/figrecipe/api/tree").status_code == 503


@pytest.mark.parametrize("mode", ["invalid", "", None])
def test_invalid_host_mode_fails_closed(hosted, mode):
    client, _ = hosted
    with override_settings(SCITEX_APP_MODE=mode):
        assert client.get("/apps/figrecipe/api/tree").status_code == 503
        assert post(client, "api/new").status_code == 503


@pytest.mark.parametrize("permission", [1, "true", None, False])
def test_only_literal_true_grants_write(hosted, permission):
    client, root = hosted

    class InvalidPermissionStorage(ProjectStorage):
        def can_write(self, project_id, request):
            return permission

    with override_settings(SCITEX_PROJECT_STORAGE=InvalidPermissionStorage(root)):
        assert client.get("/apps/figrecipe/api/tree").status_code == 200
        assert post(client, "api/compose", {"filename": "denied"}).status_code == 403
        assert post(client, "api/new").status_code == 403
    assert sorted(p.name for p in (root / "alpha").iterdir()) == ["data.txt", "outside"]


@pytest.mark.parametrize("field", ["path", "recipe", "recipe_path", "working_dir"])
def test_query_and_body_path_escape_denied(hosted, field):
    client, root = hosted
    target = str(root / "beta" / "data.txt")
    assert client.get("/apps/figrecipe/ping", {field: target}).status_code == 403
    assert post(client, "api/compose", {field: target}).status_code == 403


@pytest.mark.parametrize(
    "value", ["../beta/data.txt", "../alpha-neighbor/data.txt", "outside/data.txt"]
)
def test_endpoint_traversal_prefix_neighbor_and_symlink_denied(hosted, value):
    client, _ = hosted
    assert client.get(f"/apps/figrecipe/api/file-content/{value}").status_code == 403


def test_duplicate_query_path_is_checked(hosted):
    client, _ = hosted
    assert (
        client.get("/apps/figrecipe/ping?recipe=../beta/data.txt&recipe=").status_code
        == 403
    )


def test_file_content_uses_project_not_ambient_cwd(hosted, monkeypatch):
    client, root = hosted
    monkeypatch.chdir(root / "beta")
    response = client.get("/apps/figrecipe/api/file-content/data.txt")
    assert response.status_code == 200
    assert response.json() == {"content": "alpha"}


def test_tree_excludes_symlink_outside_project(hosted):
    client, _ = hosted
    data = client.get("/apps/figrecipe/api/tree").json()
    assert [x["name"] for x in data["tree"]] == ["data.txt"]


def test_csrf_required_even_when_host_omits_middleware(hosted):
    client, _ = hosted
    with override_settings(MIDDLEWARE=[f"{__name__}.FixtureUserMiddleware"]):
        response = client.post(
            "/apps/figrecipe/api/compose", data="{}", content_type="application/json"
        )
        assert response.status_code == 403


def test_read_only_project_can_read_but_cannot_write(hosted):
    client, _ = hosted
    assert (
        client.get("/apps/figrecipe/api/tree", HTTP_X_READ_ONLY="1").status_code == 200
    )
    assert post(client, "api/compose", {}, HTTP_X_READ_ONLY="1").status_code == 403
    assert post(client, "api/new", {}, HTTP_X_READ_ONLY="1").status_code == 403


@pytest.mark.parametrize(
    "endpoint", ["api/new", "api/gallery/demo", "api/compose", "update"]
)
def test_mutations_cannot_use_csrf_safe_method(hosted, endpoint):
    client, _ = hosted
    assert client.get(f"/apps/figrecipe/{endpoint}").status_code == 405


@pytest.mark.parametrize(
    "endpoint,body",
    [
        ("api/compose", {"filename": "../escape"}),
        ("api/gallery/add", {"template": "../escape"}),
        ("add_image_from_url", {"url": "file:///etc/passwd"}),
    ],
)
def test_wrapper_specific_guards_live_in_leaf(hosted, endpoint, body):
    client, _ = hosted
    assert post(client, endpoint, body).status_code == 403


def test_compose_without_caller_working_dir_writes_to_project(hosted, monkeypatch):
    from PIL import Image

    client, root = hosted
    monkeypatch.chdir(root / "beta")
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, "PNG")
    body = {
        "filename": "composed",
        "figures": [
            {
                "x": 0,
                "y": 0,
                "width": 2,
                "height": 2,
                "image": base64.b64encode(buffer.getvalue()).decode(),
            }
        ],
    }
    response = post(client, "api/compose", body)
    assert response.status_code == 200, response.content
    assert (root / "alpha/composed.png").exists()
    assert not (root / "beta/composed.png").exists()


def test_generated_compose_target_symlink_denied(hosted):
    client, root = hosted
    (root / "alpha/composed.png").symlink_to(root / "beta/data.txt")
    assert post(client, "api/compose", {}).status_code == 403
    assert (root / "beta/data.txt").read_text() == "beta"


def test_recipe_data_reference_checked_before_loader(hosted):
    client, root = hosted
    (root / "alpha/bad.yaml").write_text(
        "figure: {}\naxes: {}\ndata:\n  csv_format: single\n  csv_path: ../beta/data.txt\n"
    )
    assert client.get("/apps/figrecipe/ping?recipe=bad.yaml").status_code == 403
    body = {
        "recipe_content": "axes:\n  ax_0_0:\n    subpanels:\n      - axes:\n          calls:\n            - args:\n                - data: ../beta/data.csv\n"
    }
    assert post(client, "load_recipe", body).status_code == 403


def test_read_capability_and_editor_cache_are_user_project_scoped(hosted):
    from django.test import RequestFactory
    from scitex_sdk.host import ProjectAccess

    from figrecipe._django._project_access import ProjectFiles, editor_key

    _, root = hosted
    request = RequestFactory().get("/")
    request.user = types.SimpleNamespace(pk="alice")
    request._figrecipe_project = ProjectAccess("alpha", "Project alpha", root / "alpha")
    first = editor_key(request, "same.yaml")
    request.user.pk = "bob"
    assert editor_key(request, "same.yaml") != first
    files = ProjectFiles(request._figrecipe_project, root / "alpha")
    assert files.read("data.txt") == "alpha"
    with pytest.raises(Exception, match="outside the selected project"):
        files.read("outside/data.txt")


def test_legacy_prefix_retains_leaf_guard(hosted):
    client, _ = hosted
    assert client.get("/legacy/figrecipe/ping").status_code == 200
    assert (
        client.get("/legacy/figrecipe/api/file-content/../beta/data.txt").status_code
        == 403
    )


def test_standalone_retains_local_directory_and_path_selection(hosted):
    client, root = hosted
    with override_settings(SCITEX_APP_MODE="standalone", MIDDLEWARE=[]):
        response = client.get(
            "/apps/figrecipe/api/file-content/data.txt",
            {"working_dir": str(root / "beta")},
        )
        assert response.status_code == 200
        assert response.json() == {"content": "beta"}


def test_hosted_create_edit_save_datatable_and_download(hosted):
    client, root = hosted
    response = post(client, "api/new")
    assert response.status_code == 200, response.content[:300]
    recipe = response.json()["file"]
    assert (root / "alpha" / recipe).exists()
    assert client.get("/apps/figrecipe/preview", {"recipe": recipe}).status_code == 200
    response = post(client, f"save?recipe={recipe}", {"overrides": {}})
    assert response.status_code == 200, response.content[:300]
    assert (root / "alpha" / recipe).with_suffix(".overrides.json").exists()
    response = post(
        client, f"datatable/import?recipe={recipe}", {"content": "x,y\n1,2\n3,4\n"}
    )
    assert response.status_code == 200, response.content[:300]
    data = client.get("/apps/figrecipe/datatable/data", {"recipe": recipe}).json()
    assert data["source"] == "project"
    assert data["rows"] == [[1.0, 2.0], [3.0, 4.0]]
    response = client.get("/apps/figrecipe/api/download", {"recipe": recipe})
    assert response.status_code == 200
    assert b"figure:" in b"".join(response.streaming_content)


def test_loaded_editors_for_collaborators_are_distinct(hosted):
    from figrecipe._django.services import _editor_cache

    client, _ = hosted
    recipe = post(client, "api/new").json()["file"]
    assert client.get("/apps/figrecipe/preview", {"recipe": recipe}).status_code == 200
    assert (
        client.get(
            "/apps/figrecipe/preview",
            {"recipe": recipe, "project": "alpha"},
            HTTP_X_USER="bob",
        ).status_code
        == 200
    )
    editors = [value[0] for key, value in _editor_cache.items() if recipe in key]
    assert len(editors) == 2
    assert editors[0] is not editors[1]


def test_generated_new_figure_output_symlink_denied(hosted):
    client, root = hosted
    (root / "alpha/new_figure_001.png").symlink_to(root / "beta/data.txt")
    assert post(client, "api/new").status_code == 403
    assert (root / "beta/data.txt").read_text() == "beta"


def test_new_figure_checks_automatically_loaded_overrides_before_reproduction(hosted):
    client, root = hosted
    (root / "alpha/new_figure_001.overrides.json").symlink_to(root / "beta/data.txt")
    assert post(client, "api/new").status_code == 403
    assert not (root / "alpha/new_figure_001.yaml").exists()


def test_demo_scan_ignores_recipes_outside_project(hosted):
    client, root = hosted
    (root / "beta/other.yaml").write_text("figure: {}\naxes: {}\n")
    (root / "alpha/linked.yaml").symlink_to(root / "beta/other.yaml")
    response = post(client, "api/gallery/demo")
    assert response.status_code == 200, response.content
    assert response.json()["seeded"] is True
    assert (root / "alpha" / response.json()["recipe_path"]).exists()
    switched = post(client, "api/switch", {"path": response.json()["recipe_path"]})
    assert switched.status_code == 200, switched.content
    assert switched.json()["image"]


def correlation_spec():
    return {
        "schema": "scitex-stats.plot-spec",
        "version": 1,
        "kind": "correlation",
        "xy": {"x": [1, 2, 3], "y": [2, 3, 5]},
        "layers": [{"type": "scatter"}],
        "annotations": {"brackets": []},
        "style": {"width_mm": 85, "height_mm": 68},
    }


def test_hosted_stats_import_uses_selected_project(hosted, monkeypatch):
    client, root = hosted
    monkeypatch.chdir(root / "beta")
    response = post(client, "api/import/stats-plot-spec", {"spec": correlation_spec(), "name": "stats"})
    assert response.status_code == 200, response.content
    assert (root / "alpha/stats_001.yaml").exists()
    assert (root / "alpha/stats_001.png").exists()
    assert not (root / "beta/stats_001.yaml").exists()


@pytest.mark.parametrize("output", ["stats_001.png", "stats_001.tex", "stats_001_data"])
def test_stats_import_generated_targets_cannot_escape_project(hosted, output):
    client, root = hosted
    (root / "alpha" / output).symlink_to(root / "beta/data.txt")
    response = post(client, "api/import/stats-plot-spec", {"spec": correlation_spec(), "name": "stats"})
    assert response.status_code == 403, response.content
    assert (root / "beta/data.txt").read_text() == "beta"
    assert not (root / "alpha/stats_001.yaml").exists()


def test_hosted_zip_is_explicitly_unavailable(hosted):
    client, root = hosted
    (root / "alpha/recipe.zip").write_bytes(b"fixture")
    assert client.get("/apps/figrecipe/ping?recipe=recipe.zip").status_code == 501


@pytest.mark.parametrize("mount", ["/apps/figrecipe", "/legacy/figrecipe"])
def test_workspace_declares_its_actual_mount_and_leaf_assets(hosted, mount):
    client, _ = hosted
    response = client.get(mount + "/workspace/?project=alpha")
    assert response.status_code == 200, response.content[:300]
    html = response.content.decode()
    assert f'data-stx-mount="{mount}"' in html
    assert 'data-app-slug="figrecipe"' in html
    assert 'figrecipe/assets/workspace.js' in html
    assert 'data-embedded="true"' in html
    assert 'data-project-id="alpha"' in html
    assert 'data-project-name="Project alpha"' in html


def test_context_builder_uses_sdk_authority_and_requires_host_mount(hosted):
    from django.template.loader import render_to_string
    from figrecipe._django.workspace import build_workspace_context

    client, root = hosted
    request = client.get("/apps/figrecipe/?project=alpha").wsgi_request
    context = build_workspace_context(request, current_project=types.SimpleNamespace(root=root / "beta"))
    assert context["working_dir"] == str(root / "alpha")
    assert context["project_id"] == "alpha"
    assert context["project_name"] == "Project alpha"
    assert context["stx_mount"] is None
    html = render_to_string("figrecipe/workspace_partial.html", context, request=request)
    assert 'role="alert"' in html
    assert 'workspace.js' not in html
    context["stx_mount"] = ""
    html = render_to_string("figrecipe/workspace_partial.html", context, request=request)
    assert 'data-stx-mount=""' in html
    assert 'workspace.js' in html


def test_workspace_authority_failures_are_explicit(hosted):
    client, _ = hosted
    assert client.get("/apps/figrecipe/workspace/", HTTP_X_USER="").status_code == 401
    assert client.get("/apps/figrecipe/workspace/?project=beta").status_code == 404
    with override_settings(SCITEX_PROJECT_STORAGE=None):
        assert client.get("/apps/figrecipe/workspace/").status_code == 503


def test_nested_legacy_page_and_api_keep_their_mount(hosted):
    client, _ = hosted
    response = client.get("/legacy/figrecipe/figrecipe/?project=alpha")
    assert response.status_code == 200
    assert 'name="stx-mount" content="/legacy/figrecipe"' in response.content.decode()
    response = client.get("/legacy/figrecipe/figrecipe/api/files?project=alpha")
    assert response.status_code == 200


def test_theme_cannot_select_an_arbitrary_file(hosted):
    client, _ = hosted
    assert post(client, "switch_theme", {"theme": "../../escape"}).status_code == 400


def test_actual_overrides_target_symlink_denied(hosted):
    client, root = hosted
    recipe = post(client, "api/new").json()["file"]
    (root / "alpha" / recipe).with_suffix(".overrides.json").symlink_to(root / "beta/data.txt")
    assert post(client, f"save?recipe={recipe}", {"overrides": {}}).status_code == 403
    assert (root / "beta/data.txt").read_text() == "beta"


class RememberingProjectProvider(ProjectProvider):
    """Real provider state shared across the owned fixture requests."""

    selected = "beta"

    def last_visited(self, request):
        return type(self).selected

    def remember(self, request, project_id):
        type(self).selected = project_id


def test_old_project_api_request_cannot_change_the_new_navigation_selection(hosted):
    client, _ = hosted
    RememberingProjectProvider.selected = "beta"
    with override_settings(
        SCITEX_PROJECT_PROVIDER=f"{__name__}.RememberingProjectProvider"
    ):
        selected = client.get("/apps/figrecipe/?project=beta", HTTP_X_USER="bob")
        old_resource = client.get(
            "/apps/figrecipe/api/tree?project=alpha", HTTP_X_USER="bob"
        )
        following = client.get("/apps/figrecipe/workspace/", HTTP_X_USER="bob")
        contract = {
            "explicit navigation succeeds": selected.status_code == 200,
            "authorized old resource stays accessible": old_resource.status_code == 200,
            "resource cannot remember an old project": RememberingProjectProvider.selected == "beta",
            "next navigation retains the new project": b'data-project-id="beta"' in following.content,
        }
        assert all(contract.values()), contract
