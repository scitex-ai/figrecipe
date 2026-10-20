"""Canonical and established FigRecipe reverse callers share leaf views."""

import os
import types

import django
import pytest
from django.test import override_settings
from django.urls import resolve, reverse
from scitex_sdk.urls import mount_urlpatterns


@pytest.fixture(scope="module", autouse=True)
def ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()


@pytest.mark.parametrize("prefix", ["apps/figrecipe/", "custom/plot/"])
@pytest.mark.parametrize(
    "name,kwargs,suffix",
    [
        ("figure_editor", {}, ""),
        ("workspace", {}, "workspace/"),
        ("figrecipe_editor", {}, "figrecipe/"),
        ("figrecipe_api", {"endpoint": "preview"}, "figrecipe/preview"),
    ],
)
def test_both_namespaces_resolve_to_one_leaf_view(prefix, name, kwargs, suffix):
    # Arrange
    contract = {}
    # Act
    root = types.ModuleType("figrecipe_compat_root")
    root.urlpatterns = mount_urlpatterns(prefix, "figrecipe._django.urls")
    with override_settings(ROOT_URLCONF=root):
        canonical = reverse("figrecipe:" + name, kwargs=kwargs)
        legacy = reverse("figrecipe_app:" + name, kwargs=kwargs)
        contract["1: canonical == legacy == '/' + prefix + suffix"] = bool(
            canonical == legacy == "/" + prefix + suffix
        )
        contract["2: resolve(canonical).func is resolve(legacy).func"] = bool(
            resolve(canonical).func is resolve(legacy).func
        )
    # Assert
    assert all(contract.values()), contract


def test_standalone_preserves_plain_and_both_namespaced_callers():
    # Arrange
    contract = {}
    # Act
    with override_settings(ROOT_URLCONF="figrecipe._django.urls_standalone"):
        contract[
            "1: reverse('editor') == reverse('figrecipe:editor') == reverse('figrecipe_app:editor') == '/'"
        ] = bool(
            reverse("editor")
            == reverse("figrecipe:editor")
            == reverse("figrecipe_app:editor")
            == "/"
        )
        contract[
            "2: reverse('workspace') == reverse('figrecipe:workspace') == reverse('figrecipe_app:workspace') == '/workspace/'"
        ] = bool(
            reverse("workspace")
            == reverse("figrecipe:workspace")
            == reverse("figrecipe_app:workspace")
            == "/workspace/"
        )
    # Assert
    assert all(contract.values()), contract
