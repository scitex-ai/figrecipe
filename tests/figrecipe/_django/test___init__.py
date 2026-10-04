"""Generic discovery preserves lazy leaf targets and their real boundaries."""

import importlib
import json
import subprocess
import sys
from types import SimpleNamespace

from django.test import RequestFactory
from django.utils.module_loading import import_string

pytest_plugins = ("tests.integration.test_project_capability",)

_EXPECTED = {
    "INSTALLED_APPS_ENTRIES": tuple,
    "context_builder": str,
    "partial_template": str,
    "content_renderer": str,
    "api_policy_module": str,
    "hosted_api_dispatcher": str,
}


def _declarations():
    from scitex_sdk.app.plugins import leaf_declarations

    return leaf_declarations("figrecipe._django", _EXPECTED)


def test_declarations_survive_loading_the_policy_submodule():
    # Arrange
    before = _declarations()
    # Act
    importlib.import_module(before["api_policy_module"])
    after = _declarations()
    # Assert
    assert before == after and set(after) == set(_EXPECTED)


def test_package_declarations_do_not_require_sdk_django_or_views():
    # Arrange
    code = """
import importlib.abc
import sys
class NoGUI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'django', 'scitex_sdk'}:
            raise ModuleNotFoundError('GUI unavailable', name=fullname)
sys.meta_path.insert(0, NoGUI())
import figrecipe._django as app
assert isinstance(app.content_renderer, str)
assert isinstance(app.hosted_api_dispatcher, str)
assert isinstance(app.INSTALLED_APPS_ENTRIES, tuple)
assert 'figrecipe._django.views' not in sys.modules
"""
    # Act
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=20
    )
    # Assert
    assert result.returncode == 0, result.stderr


def test_discovered_renderer_uses_authority_and_the_declared_api_mount(hosted):
    # Arrange
    client, root = hosted
    request = client.get("/apps/figrecipe/workspace/?project=alpha").wsgi_request
    renderer = import_string(_declarations()["content_renderer"])
    presentation = SimpleNamespace(root=root / "beta")
    api_mount = "/apps/figrecipe/figrecipe"
    # Act
    response = renderer(request, presentation, stx_mount=api_mount)
    html = response.content.decode()
    # Assert
    assert {
        "status": response.status_code,
        "API mount": f'data-stx-mount="{api_mount}"' in html,
        "authorized root": f'data-working-dir="{root / "alpha"}"' in html,
        "CSRF cookie": "csrftoken" in response.cookies,
    } == {
        "status": 200,
        "API mount": True,
        "authorized root": True,
        "CSRF cookie": True,
    }


def test_discovered_hosted_dispatcher_keeps_read_and_csrf_boundaries(hosted):
    # Arrange
    client, _ = hosted
    request = client.get("/apps/figrecipe/ping?project=alpha").wsgi_request
    dispatcher = import_string(_declarations()["hosted_api_dispatcher"])
    unsafe = RequestFactory().post(
        "/apps/figrecipe/figrecipe/api/switch?project=alpha",
        data=json.dumps({"project": "alpha"}),
        content_type="application/json",
    )
    unsafe.user = request.user
    # Act
    read_response = dispatcher(request, "ping")
    csrf_response = dispatcher(unsafe, "api/switch")
    # Assert
    assert {
        "read": read_response.status_code,
        "missing CSRF": csrf_response.status_code,
        "CSRF refusal": b"CSRF" in csrf_response.content,
    } == {"read": 200, "missing CSRF": 403, "CSRF refusal": True}
