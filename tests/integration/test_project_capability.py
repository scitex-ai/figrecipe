"""Real HTTP boundary tests with SDK providers and isolated local project files."""

import json
import os
import types
from contextlib import contextmanager

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


@contextmanager
def in_directory(path):
    """Use the actual owned cwd, restoring it even when a request fails."""
    previous = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


def test_shell_declares_mount_scope_and_host_provider(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    html = client.get("/apps/figrecipe/").content.decode()
    contract['1: \'name="stx-mount" content="/apps/figrecipe"\' in html'] = bool(
        'name="stx-mount" content="/apps/figrecipe"' in html
    )
    contract["2: html.count('name=\"stx-app-scope\"') == 1"] = bool(
        html.count('name="stx-app-scope"') == 1
    )
    contract["3: 'name=\"stx-project-provider\"' in html"] = bool(
        'name="stx-project-provider"' in html
    )
    contract["4: 'data-hosted=\"true\"' in html"] = bool('data-hosted="true"' in html)
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize(
    "url", ["/apps/figrecipe/", "/apps/figrecipe/ping", "/apps/figrecipe/api/tree"]
)
def test_anonymous_denied_before_file_io(hosted, url):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert client.get(url, HTTP_X_USER="").status_code == 401


def test_explicit_other_project_does_not_fall_back(hosted):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert client.get("/apps/figrecipe/api/tree?project=beta").status_code == 404


def test_missing_provider_fails_closed(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    with override_settings(SCITEX_PROJECT_STORAGE=None):
        contract["1: client.get('/apps/figrecipe/api/tree').status_code == 503"] = bool(
            client.get("/apps/figrecipe/api/tree").status_code == 503
        )
    with override_settings(SCITEX_PROJECT_PROVIDER=None):
        contract["2: client.get('/apps/figrecipe/api/tree').status_code == 503"] = bool(
            client.get("/apps/figrecipe/api/tree").status_code == 503
        )
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize("mode", ["invalid", "", None])
def test_invalid_host_mode_fails_closed(hosted, mode):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    with override_settings(SCITEX_APP_MODE=mode):
        contract["1: client.get('/apps/figrecipe/api/tree').status_code == 503"] = bool(
            client.get("/apps/figrecipe/api/tree").status_code == 503
        )
        contract["2: post(client, 'api/new').status_code == 503"] = bool(
            post(client, "api/new").status_code == 503
        )
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize("permission", [1, "true", None, False])
def test_only_literal_true_grants_write(hosted, permission):
    # Arrange
    contract = {}
    # Act
    client, root = hosted

    class InvalidPermissionStorage(ProjectStorage):
        def can_write(self, project_id, request):
            return permission

    with override_settings(SCITEX_PROJECT_STORAGE=InvalidPermissionStorage(root)):
        contract["2: client.get('/apps/figrecipe/api/tree').status_code == 200"] = bool(
            client.get("/apps/figrecipe/api/tree").status_code == 200
        )
        contract[
            "3: post(client, 'api/compose', {'filename': 'denied'}).status_code == 403"
        ] = bool(post(client, "api/compose", {"filename": "denied"}).status_code == 403)
        contract["4: post(client, 'api/new').status_code == 403"] = bool(
            post(client, "api/new").status_code == 403
        )
    contract[
        "1: sorted((p.name for p in (root / 'alpha').iterdir())) == ['data.txt', 'outside']"
    ] = bool(
        sorted(p.name for p in (root / "alpha").iterdir()) == ["data.txt", "outside"]
    )
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize("field", ["path", "recipe", "recipe_path", "working_dir"])
def test_query_and_body_path_escape_denied(hosted, field):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    target = str(root / "beta" / "data.txt")
    contract[
        "1: client.get('/apps/figrecipe/ping', {field: target}).status_code == 403"
    ] = bool(client.get("/apps/figrecipe/ping", {field: target}).status_code == 403)
    contract["2: post(client, 'api/compose', {field: target}).status_code == 403"] = (
        bool(post(client, "api/compose", {field: target}).status_code == 403)
    )
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize(
    "value", ["../beta/data.txt", "../alpha-neighbor/data.txt", "outside/data.txt"]
)
def test_endpoint_traversal_prefix_neighbor_and_symlink_denied(hosted, value):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert client.get(f"/apps/figrecipe/api/file-content/{value}").status_code == 403


def test_duplicate_query_path_is_checked(hosted):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert (
        client.get("/apps/figrecipe/ping?recipe=../beta/data.txt&recipe=").status_code
        == 403
    )


def test_file_content_uses_project_not_ambient_cwd(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    with in_directory(root / "beta"):
        response = client.get("/apps/figrecipe/api/file-content/data.txt")
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    contract["2: response.json() == {'content': 'alpha'}"] = bool(
        response.json() == {"content": "alpha"}
    )
    # Assert
    assert all(contract.values()), contract


def test_tree_excludes_symlink_outside_project(hosted):
    # Arrange
    client, _ = hosted
    data = client.get("/apps/figrecipe/api/tree").json()
    # Act
    # Assert
    assert [x["name"] for x in data["tree"]] == ["data.txt"]


def test_csrf_required_even_when_host_omits_middleware(hosted):
    # Arrange
    client, _ = hosted
    with override_settings(MIDDLEWARE=[f"{__name__}.FixtureUserMiddleware"]):
        response = client.post(
            "/apps/figrecipe/api/compose", data="{}", content_type="application/json"
        )
        # Act
        # Assert
        assert response.status_code == 403


def test_read_only_project_can_read_but_cannot_write(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    contract[
        "1: client.get('/apps/figrecipe/api/tree', HTTP_X_READ_ONLY='1').status_code == 200"
    ] = bool(
        client.get("/apps/figrecipe/api/tree", HTTP_X_READ_ONLY="1").status_code == 200
    )
    contract[
        "2: post(client, 'api/compose', {}, HTTP_X_READ_ONLY='1').status_code == 403"
    ] = bool(post(client, "api/compose", {}, HTTP_X_READ_ONLY="1").status_code == 403)
    contract[
        "3: post(client, 'api/new', {}, HTTP_X_READ_ONLY='1').status_code == 403"
    ] = bool(post(client, "api/new", {}, HTTP_X_READ_ONLY="1").status_code == 403)
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize(
    "endpoint", ["api/new", "api/gallery/demo", "api/compose", "update"]
)
def test_mutations_cannot_use_csrf_safe_method(hosted, endpoint):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
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
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert post(client, endpoint, body).status_code == 403


def test_read_capability_and_editor_cache_are_user_project_scoped(hosted):
    # Arrange
    contract = {}
    # Act
    from django.test import RequestFactory
    from scitex_sdk.host import ProjectAccess

    from figrecipe._django._project_access import ProjectFiles, editor_key

    _, root = hosted
    request = RequestFactory().get("/")
    request.user = types.SimpleNamespace(pk="alice")
    request._figrecipe_project = ProjectAccess("alpha", "Project alpha", root / "alpha")
    first = editor_key(request, "same.yaml")
    request.user.pk = "bob"
    contract["1: editor_key(request, 'same.yaml') != first"] = bool(
        editor_key(request, "same.yaml") != first
    )
    files = ProjectFiles(request._figrecipe_project, root / "alpha")
    contract["2: files.read('data.txt') == 'alpha'"] = bool(
        files.read("data.txt") == "alpha"
    )
    # Assert
    assert all(contract.values()), contract


def test_read_capability_rejects_project_escape(hosted):
    # Arrange
    from scitex_sdk.host import ProjectAccess

    from figrecipe._django._project_access import ProjectFiles

    _, root = hosted
    access = ProjectAccess("alpha", "Project alpha", root / "alpha")
    files = ProjectFiles(access, root / "alpha")
    # Act
    # Assert
    with pytest.raises(Exception, match="outside the selected project"):
        files.read("outside/data.txt")


def test_legacy_prefix_retains_leaf_guard(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    contract["1: client.get('/legacy/figrecipe/ping').status_code == 200"] = bool(
        client.get("/legacy/figrecipe/ping").status_code == 200
    )
    contract[
        "2: client.get('/legacy/figrecipe/api/file-content/../beta/data.txt').status_code == 403"
    ] = bool(
        client.get("/legacy/figrecipe/api/file-content/../beta/data.txt").status_code
        == 403
    )
    # Assert
    assert all(contract.values()), contract


def test_standalone_retains_local_directory_and_path_selection(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    with override_settings(SCITEX_APP_MODE="standalone", MIDDLEWARE=[]):
        response = client.get(
            "/apps/figrecipe/api/file-content/data.txt",
            {"working_dir": str(root / "beta")},
        )
        contract["1: response.status_code == 200"] = bool(response.status_code == 200)
        contract["2: response.json() == {'content': 'beta'}"] = bool(
            response.json() == {"content": "beta"}
        )
    # Assert
    assert all(contract.values()), contract
