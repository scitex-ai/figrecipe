#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guards for the Template Gallery's package-relative asset resolution.

The gallery once resolved its assets by climbing OUT of the package
(``_PKG_ROOT.parents[1] / "examples" / "02_plot_and_reproduce_all_out"``).
That happens to land on the repo root in a src-layout checkout, so it worked
for developers and failed in every installed deployment: a wheel install
resolved it to ``<venv>/lib/python3.12/examples/...``, which does not exist,
so every declared template was filtered out and the panel rendered
"No templates available for this category" with an HTTP 200 and no log line.

These tests fail when the gallery resolves ZERO templates, and they fail on
the mechanism that actually broke — the path is derived from the IMPORTED
``figrecipe`` package location, so an install that ships the code without the
assets goes red here rather than in front of a user.

The handler module is loaded by file path rather than imported normally
because ``figrecipe._django.handlers.__init__`` imports Django models, which
require a configured app registry (``ImproperlyConfigured: Requested setting
INSTALLED_APPS``). ``gallery.py`` itself only needs ``django.http``, so
loading it directly exercises the real production module with no test-only
substitute standing in for anything.
"""

import importlib.util
from pathlib import Path

import pytest


def _package_root() -> Path:
    """Directory of the IMPORTED figrecipe package (wheel, editable, or src)."""
    import figrecipe

    return Path(figrecipe.__file__).resolve().parent


def _load_gallery_module():
    path = _package_root() / "_django" / "handlers" / "gallery.py"
    if not path.exists():
        pytest.fail(f"gallery handler missing from the installed package: {path}")
    spec = importlib.util.spec_from_file_location(
        "figrecipe_gallery_under_test", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gallery():
    return _load_gallery_module()


def test_templates_dir_is_inside_the_package(gallery):
    """The asset dir must be package data, not a path outside the package.

    This is the invariant that makes the gallery survive installation: an
    asset resolved by climbing above the package root is only correct by
    accident of the developer's directory layout.
    """
    # Arrange
    pkg_root = _package_root()

    # Act
    resolved = gallery.TEMPLATES_DIR.resolve()

    # Assert
    assert pkg_root in resolved.parents, (
        f"gallery assets resolve OUTSIDE the package: {resolved} is not under "
        f"{pkg_root}. A path that leaves the package root breaks on install."
    )


def test_templates_dir_exists(gallery):
    # Arrange
    templates_dir = gallery.TEMPLATES_DIR

    # Act
    exists = templates_dir.is_dir()

    # Assert
    assert exists, (
        f"gallery asset directory does not exist: {templates_dir}. The package "
        "was built without its gallery_templates package data."
    )


def test_gallery_resolves_more_than_zero_templates(gallery):
    """THE guard: zero resolved templates is the production failure itself."""
    # Arrange
    declared = sum(len(v) for v in gallery.GALLERY_TEMPLATES.values())

    # Act
    categories = gallery.available_categories()
    resolved = sum(len(v) for v in categories.values())

    # Assert
    assert resolved > 0, (
        f"gallery resolved ZERO of {declared} declared templates from "
        f"{gallery.TEMPLATES_DIR} — this is exactly the "
        "'No templates available for this category' bug."
    )


def test_gallery_resolves_every_declared_template(gallery):
    """No declared template may be silently dropped for a missing asset."""
    # Arrange
    declared_names = {
        tmpl["name"]
        for templates in gallery.GALLERY_TEMPLATES.values()
        for tmpl in templates
    }

    # Act
    missing = sorted(
        name
        for name in declared_names
        if not (gallery.TEMPLATES_DIR / f"{name}.yaml").exists()
    )

    # Assert
    assert missing == [], f"declared templates with no shipped recipe: {missing}"


def test_every_resolved_template_path_exists(gallery):
    # Arrange
    categories = gallery.available_categories()

    # Act
    bad = [
        item["path"]
        for items in categories.values()
        for item in items
        if not Path(item["path"]).exists()
    ]

    # Assert
    assert bad == [], f"gallery advertised paths that do not exist: {bad}"


def test_every_resolved_template_has_a_thumbnail(gallery):
    """A missing PNG degrades to an icon rather than emptying the gallery,
    so this is a quality guard, not a correctness one — but a grant demo
    should not fall back to icons."""
    # Arrange
    categories = gallery.available_categories()

    # Act
    without = sorted(
        item["name"]
        for items in categories.values()
        for item in items
        if not item["has_thumbnail"]
    )

    # Assert
    assert without == [], f"shipped templates missing a thumbnail PNG: {without}"


def test_data_backed_templates_ship_their_data_files(gallery):
    """A recipe whose YAML references ``<name>_data/...`` must ship that data.

    ``handle_gallery_add`` copies ``<name>_data`` next to the recipe. Shipping
    the recipe without it lists fine and then fails on "Add to canvas" — a
    worse demo failure than an empty panel, because it fails after a click.
    """
    # Arrange
    declared_names = sorted(
        {
            tmpl["name"]
            for templates in gallery.GALLERY_TEMPLATES.values()
            for tmpl in templates
        }
    )

    # Act
    broken = []
    for name in declared_names:
        yaml_path = gallery.TEMPLATES_DIR / f"{name}.yaml"
        if not yaml_path.exists():
            continue
        text = yaml_path.read_text(encoding="utf-8", errors="replace")
        data_dir = gallery.TEMPLATES_DIR / f"{name}_data"
        if f"{name}_data/" in text and not data_dir.is_dir():
            broken.append(name)

    # Assert
    assert broken == [], (
        "templates reference a data directory that was not shipped "
        f"(Add-to-canvas would fail): {broken}"
    )


# EOF
