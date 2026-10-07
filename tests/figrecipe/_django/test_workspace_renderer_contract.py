"""Leaf rendering through the genuine SDK adapter and project authority."""

from types import SimpleNamespace

import pytest
from django.conf import settings
from django.test import override_settings
from scitex_sdk.host import AccessError

pytest_plugins = ("tests.integration.test_project_capability",)


@pytest.mark.parametrize("mount", ["", "/declared/figrecipe"])
def test_partial_renderer_uses_authorized_project_and_explicit_mount(hosted, mount):
    # Arrange
    from figrecipe._django.workspace import render_workspace_content

    client, root = hosted
    request = client.get("/apps/figrecipe/workspace/?project=alpha").wsgi_request
    presentation_project = SimpleNamespace(root=root / "beta")
    # Act
    response = render_workspace_content(request, presentation_project, stx_mount=mount)
    html = response.content.decode()
    # Assert
    assert {
        "status": response.status_code,
        "mount": f'data-stx-mount="{mount}"' in html,
        "project": 'data-project-id="alpha"' in html,
        "working directory": f'data-working-dir="{root / "alpha"}"' in html,
        "leaf entry": "figrecipe/assets/workspace.js" in html,
        "csrf cookie": "csrftoken" in response.cookies,
    } == {
        "status": 200,
        "mount": True,
        "project": True,
        "working directory": True,
        "leaf entry": True,
        "csrf cookie": True,
    }


def test_partial_renderer_requires_an_explicit_mount(hosted):
    # Arrange
    from figrecipe._django.workspace import render_workspace_content

    client, _ = hosted
    request = client.get("/apps/figrecipe/workspace/?project=alpha").wsgi_request
    # Act: invoke the renderer inside the exception check.
    # Assert: reject an undeclared mount with the expected error.
    with pytest.raises(TypeError, match="explicitly declare the app mount"):
        render_workspace_content(request, stx_mount=None)


def test_partial_renderer_rejects_anonymous_project_access(hosted):
    # Arrange
    from figrecipe._django.workspace import render_workspace_content

    client, _ = hosted
    request = client.get(
        "/apps/figrecipe/workspace/?project=alpha", HTTP_X_USER=""
    ).wsgi_request
    # Act: invoke the renderer inside the exception check.
    # Assert: reject anonymous project authority with the expected error.
    with pytest.raises(AccessError, match="Authentication required"):
        render_workspace_content(request, stx_mount="/apps/figrecipe")


@pytest.mark.parametrize("route", ["/apps/figrecipe/", "/apps/figrecipe/workspace/"])
def test_shell_view_uses_host_shadowed_sdk_app_adapter(hosted, tmp_path, route):
    # Arrange
    client, _ = hosted
    template_root = tmp_path / "host-templates"
    adapter = template_root / "scitex_sdk/app/app_shell.html"
    adapter.parent.mkdir(parents=True)
    adapter.write_text(
        '{% extends "scitex_sdk/ui/standalone_shell.html" %}'
        '{% block app_content %}<section data-host-adapter="true">'
        "{% block scitex_app_content %}{% endblock %}</section>{% endblock %}"
    )
    templates = [
        {**backend, "DIRS": [str(template_root), *backend.get("DIRS", [])]}
        for backend in settings.TEMPLATES
    ]
    # Act
    with override_settings(TEMPLATES=templates):
        response = client.get(route + "?project=alpha")
    html = response.content.decode()
    # Assert
    assert {
        "status": response.status_code,
        "host adapter": 'data-host-adapter="true"' in html,
        "leaf content": 'data-working-dir="' in html,
        "authorized project": str(tmp_path / "alpha") in html,
    } == {
        "status": 200,
        "host adapter": True,
        "leaf content": True,
        "authorized project": True,
    }
