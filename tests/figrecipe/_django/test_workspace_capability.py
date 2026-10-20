"""Real workspace authority and stale-request controls using the owned provider."""

import types

import pytest
from django.test import override_settings

from tests.integration.test_project_capability import (  # noqa: F401 - fixture registration
    ProjectProvider,
    hosted,
    post,
)


@pytest.mark.parametrize("mount", ["/apps/figrecipe", "/legacy/figrecipe"])
def test_workspace_declares_its_actual_mount_and_leaf_assets(hosted, mount):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    response = client.get(mount + "/workspace/?project=alpha")
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    html = response.content.decode()
    contract["2: f'data-stx-mount=\"{mount}\"' in html"] = bool(
        f'data-stx-mount="{mount}"' in html
    )
    contract["3: 'data-app-slug=\"figrecipe\"' in html"] = bool(
        'data-app-slug="figrecipe"' in html
    )
    contract["4: 'figrecipe/assets/workspace.js' in html"] = bool(
        "figrecipe/assets/workspace.js" in html
    )
    contract["5: 'data-embedded=\"true\"' in html"] = bool(
        'data-embedded="true"' in html
    )
    contract["6: 'data-project-id=\"alpha\"' in html"] = bool(
        'data-project-id="alpha"' in html
    )
    contract["7: 'data-project-name=\"Project alpha\"' in html"] = bool(
        'data-project-name="Project alpha"' in html
    )
    # Assert
    assert all(contract.values()), contract


def test_context_builder_uses_sdk_authority_and_requires_host_mount(hosted):
    # Arrange
    contract = {}
    # Act
    from django.template.loader import render_to_string

    from figrecipe._django.workspace import build_workspace_context

    client, root = hosted
    request = client.get("/apps/figrecipe/?project=alpha").wsgi_request
    context = build_workspace_context(
        request, current_project=types.SimpleNamespace(root=root / "beta")
    )
    contract["1: context['working_dir'] == str(root / 'alpha')"] = bool(
        context["working_dir"] == str(root / "alpha")
    )
    contract["2: context['project_id'] == 'alpha'"] = bool(
        context["project_id"] == "alpha"
    )
    contract["3: context['project_name'] == 'Project alpha'"] = bool(
        context["project_name"] == "Project alpha"
    )
    contract["4: context['stx_mount'] is None"] = bool(context["stx_mount"] is None)
    html = render_to_string(
        "figrecipe/workspace_partial.html", context, request=request
    )
    contract["5: 'role=\"alert\"' in html"] = bool('role="alert"' in html)
    contract["6: 'workspace.js' not in html"] = bool("workspace.js" not in html)
    context["stx_mount"] = ""
    html = render_to_string(
        "figrecipe/workspace_partial.html", context, request=request
    )
    contract["7: 'data-stx-mount=\"\"' in html"] = bool('data-stx-mount=""' in html)
    contract["8: 'workspace.js' in html"] = bool("workspace.js" in html)
    # Assert
    assert all(contract.values()), contract


def test_workspace_authority_failures_are_explicit(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    contract[
        "1: client.get('/apps/figrecipe/workspace/', HTTP_X_USER='').status_code == 401"
    ] = bool(
        client.get("/apps/figrecipe/workspace/", HTTP_X_USER="").status_code == 401
    )
    contract[
        "2: client.get('/apps/figrecipe/workspace/?project=beta').status_code == 404"
    ] = bool(client.get("/apps/figrecipe/workspace/?project=beta").status_code == 404)
    with override_settings(SCITEX_PROJECT_STORAGE=None):
        contract["3: client.get('/apps/figrecipe/workspace/').status_code == 503"] = (
            bool(client.get("/apps/figrecipe/workspace/").status_code == 503)
        )
    # Assert
    assert all(contract.values()), contract


def test_nested_legacy_page_and_api_keep_their_mount(hosted):
    # Arrange
    contract = {}
    # Act
    client, _ = hosted
    response = client.get("/legacy/figrecipe/figrecipe/?project=alpha")
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    contract[
        '2: \'name="stx-mount" content="/legacy/figrecipe"\' in response.content.decode()'
    ] = bool(
        'name="stx-mount" content="/legacy/figrecipe"' in response.content.decode()
    )
    response = client.get("/legacy/figrecipe/figrecipe/api/files?project=alpha")
    contract["3: response.status_code == 200"] = bool(response.status_code == 200)
    # Assert
    assert all(contract.values()), contract


def test_theme_cannot_select_an_arbitrary_file(hosted):
    # Arrange
    client, _ = hosted
    # Act
    # Assert
    assert post(client, "switch_theme", {"theme": "../../escape"}).status_code == 400


def test_actual_overrides_target_symlink_denied(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    recipe = post(client, "api/new").json()["file"]
    (root / "alpha" / recipe).with_suffix(".overrides.json").symlink_to(
        root / "beta/data.txt"
    )
    contract[
        "1: post(client, f'save?recipe={recipe}', {'overrides': {}}).status_code == 403"
    ] = bool(
        post(client, f"save?recipe={recipe}", {"overrides": {}}).status_code == 403
    )
    contract["2: (root / 'beta/data.txt').read_text() == 'beta'"] = bool(
        (root / "beta/data.txt").read_text() == "beta"
    )
    # Assert
    assert all(contract.values()), contract


class RememberingProjectProvider(ProjectProvider):
    """Real provider state shared across the owned fixture requests."""

    selected = "beta"

    def last_visited(self, request):
        return type(self).selected

    def remember(self, request, project_id):
        type(self).selected = project_id


def test_old_project_api_request_cannot_change_the_new_navigation_selection(hosted):
    # Arrange
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
            "resource cannot remember an old project": RememberingProjectProvider.selected
            == "beta",
            "next navigation retains the new project": b'data-project-id="beta"'
            in following.content,
        }
        # Act
        # Assert
        assert all(contract.values()), contract
