#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: clicking a gallery template actually PLOTS, and an empty workspace
opens on a figure.

WHY THESE TESTS EXIST
---------------------
The gallery already had guards for its assets: the panel resolves templates
(``test_gallery.py``) and the built wheel carries the recipes, thumbnails and
data files (``tests/develop/test__gallery_templates_packaged.py``). Every one
of them was green while a click produced nothing, because none of them drove
the CLICK. A click is TWO requests — ``api/gallery/add`` then ``api/switch`` —
and the defect lived in the disagreement BETWEEN them, which no
single-endpoint test can see.

The other half of why it stayed hidden: on a developer's machine the server's
cwd IS the workspace, so the two agreed by accident. These tests therefore
always run with cwd DELIBERATELY different from the workspace, which is the
normal condition in every deployment (a hosted editor runs from its Django
project root; ``figrecipe-editor --dir X`` runs from wherever it was
launched).

``test_the_workspace_is_not_the_server_cwd`` is the positive control: it
asserts the fixture really does separate the two directories, so a refactor
that quietly made them the same would not turn this whole file into a test of
nothing.
"""

import json
import os
import shutil
from pathlib import Path

import django
import pytest

os.environ.setdefault("MPLBACKEND", "Agg")


def _make_client():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")
    django.setup()
    from django.conf import settings
    from django.test import Client

    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]
    return Client()


@pytest.fixture(scope="module")
def client():
    """A Django test client for the standalone figrecipe app."""
    return _make_client()


@pytest.fixture
def split_workspace(tmp_path):
    """A workspace that is NOT the server's cwd — the deployed shape.

    Yields ``(workspace, server_cwd)``. ``FIGRECIPE_WORKING_DIR`` is set to
    the workspace exactly as ``figrecipe-editor --dir`` sets it, and the
    process really does chdir into a different directory: both are the real
    inputs the handlers read, not a stand-in for them.
    """
    workspace = tmp_path / "workspace"
    server_cwd = tmp_path / "server_cwd"
    workspace.mkdir()
    server_cwd.mkdir()

    previous_cwd = Path.cwd()
    previous_env = os.environ.get("FIGRECIPE_WORKING_DIR")
    os.environ["FIGRECIPE_WORKING_DIR"] = str(workspace)
    os.chdir(server_cwd)
    try:
        yield workspace, server_cwd
    finally:
        os.chdir(previous_cwd)
        server_cwd.chmod(0o700)
        if previous_env is None:
            os.environ.pop("FIGRECIPE_WORKING_DIR", None)
        else:
            os.environ["FIGRECIPE_WORKING_DIR"] = previous_env


@pytest.fixture
def unwritable_server_cwd(split_workspace):
    """``split_workspace`` with the server's cwd made read-only."""
    workspace, server_cwd = split_workspace
    if os.geteuid() == 0:
        pytest.skip("root ignores the write bit; the read-only cwd is not real")
    server_cwd.chmod(0o500)
    yield workspace, server_cwd


@pytest.fixture
def locked_workspace(tmp_path):
    """A workspace the server cannot write into."""
    if os.geteuid() == 0:
        pytest.skip("root ignores the write bit; the locked dir is not real")
    workspace = tmp_path / "locked"
    workspace.mkdir()
    previous_env = os.environ.get("FIGRECIPE_WORKING_DIR")
    os.environ["FIGRECIPE_WORKING_DIR"] = str(workspace)
    workspace.chmod(0o500)
    try:
        yield workspace
    finally:
        workspace.chmod(0o700)
        if previous_env is None:
            os.environ.pop("FIGRECIPE_WORKING_DIR", None)
        else:
            os.environ["FIGRECIPE_WORKING_DIR"] = previous_env


def _post(client, endpoint, workspace, payload):
    return client.post(
        f"/{endpoint}?working_dir={workspace}",
        data=json.dumps(payload),
        content_type="application/json",
    )


def _switch(client, workspace, recipe_path):
    return client.post(
        f"/api/switch?dpi=100&working_dir={workspace}",
        data=json.dumps({"path": recipe_path, "dark_mode": False}),
        content_type="application/json",
    )


def _click_template(client, workspace, template="plot_plot"):
    """Drive the exact two requests the UI issues for one template click."""
    added = _post(client, "api/gallery/add", workspace, {"template": template})
    if added.status_code != 200:
        return None, added
    recipe_path = json.loads(added.content)["recipe_path"]
    return recipe_path, _switch(client, workspace, recipe_path)


def _seed_demo(client, workspace):
    return json.loads(_post(client, "api/gallery/demo", workspace, {}).content)


# ---------------------------------------------------------------------------
# Positive control — the fixture must really separate the two directories
# ---------------------------------------------------------------------------


def test_the_workspace_is_not_the_server_cwd(split_workspace):
    # Arrange
    workspace, _ = split_workspace

    # Act
    cwd = Path.cwd().resolve()

    # Assert
    assert cwd != workspace.resolve()


def test_the_process_really_chdirs_into_the_server_cwd(split_workspace):
    # Arrange
    _, server_cwd = split_workspace

    # Act
    cwd = Path.cwd().resolve()

    # Assert
    assert cwd == server_cwd.resolve()


# ---------------------------------------------------------------------------
# Clicking a template
# ---------------------------------------------------------------------------


def test_gallery_add_writes_the_recipe_into_the_workspace(
    client, split_workspace
):
    # Arrange
    workspace, _ = split_workspace

    # Act
    _post(client, "api/gallery/add", workspace, {"template": "plot_plot"})

    # Assert
    assert (workspace / "plot_plot.yaml").is_file()


def test_gallery_add_leaves_the_server_cwd_untouched(client, split_workspace):
    # Arrange — this directory is shared by every user of a hosted editor and
    # is not the user's project on ANY deployment.
    workspace, server_cwd = split_workspace

    # Act
    _post(client, "api/gallery/add", workspace, {"template": "plot_plot"})

    # Assert
    assert sorted(p.name for p in server_cwd.iterdir()) == []


def test_gallery_add_brings_the_data_directory_with_the_recipe(
    client, split_workspace
):
    # Arrange — a recipe names its data relative to its own parent, so a
    # recipe copied alone loads and then dies in the loader.
    workspace, _ = split_workspace

    # Act
    _post(client, "api/gallery/add", workspace, {"template": "plot_plot"})

    # Assert
    assert sorted(
        p.name for p in (workspace / "plot_plot_data").glob("*.csv")
    ) == ["cos_x.csv", "cos_y.csv", "sin_x.csv", "sin_y.csv"]


def test_clicking_a_template_renders_a_figure(client, split_workspace):
    # Arrange
    workspace, _ = split_workspace

    # Act
    _, switched = _click_template(client, workspace)

    # Assert
    assert json.loads(switched.content).get("image"), switched.content[:400]


def test_clicking_a_template_keeps_the_session_in_the_users_workspace(
    client, split_workspace
):
    # Arrange — the old relative-path fallback answered 200 while silently
    # moving the session's working_dir onto the server's directory.
    workspace, _ = split_workspace

    # Act
    _, switched = _click_template(client, workspace)

    # Assert
    assert (
        Path(json.loads(switched.content)["working_dir"]).resolve()
        == workspace.resolve()
    )


def test_every_template_the_gallery_offers_can_be_clicked(
    client, split_workspace, tmp_path
):
    """Offering a template whose data does not resolve is the same dead end.

    The gallery lists a template when its yaml exists, so an asset that ships
    without its data still appears — and only fails at the click.
    """
    # Arrange
    workspace, _ = split_workspace
    listed = client.get(f"/api/gallery?working_dir={workspace}")
    categories = json.loads(listed.content)["categories"]
    names = sorted({t["name"] for items in categories.values() for t in items})

    # Act
    failures = []
    for name in names:
        target = tmp_path / f"ws_{name}"
        target.mkdir()
        _, switched = _click_template(client, target, template=name)
        if not json.loads(switched.content).get("image"):
            failures.append((name, switched.status_code, switched.content[:160]))

    # Assert
    assert not failures, f"templates that do not plot when clicked: {failures}"


def test_the_gallery_offers_templates_at_all(client, split_workspace):
    """Positive control for the sweep above: an empty list would pass it."""
    # Arrange
    workspace, _ = split_workspace

    # Act
    categories = json.loads(
        client.get(f"/api/gallery?working_dir={workspace}").content
    )["categories"]

    # Assert
    assert {t["name"] for items in categories.values() for t in items}


def test_a_read_only_server_cwd_does_not_break_the_click(
    client, unwritable_server_cwd
):
    """The server's cwd is irrelevant to a click — including unwritable.

    This is the shape that turned the bug into a VISIBLE failure rather than
    a silent misplacement: an image layer or a root-owned cwd makes the old
    ``shutil.copy2(..., Path.cwd() / ...)`` raise, the dispatcher turns that
    into a 500, and the UI reports "Failed to add template".
    """
    # Arrange
    workspace, _ = unwritable_server_cwd

    # Act
    _, switched = _click_template(client, workspace)

    # Assert
    assert json.loads(switched.content).get("image"), switched.content[:400]


def test_switch_refuses_a_recipe_that_is_not_in_the_workspace(
    client, split_workspace
):
    """A miss 404s instead of being answered from the server's directory.

    The old fallback retried ANY missed relative path against the process
    cwd, so a stray file in the server's directory answered for the user's
    workspace — which is how the misplaced template still appeared to work.
    """
    # Arrange
    workspace, server_cwd = split_workspace
    shutil.copy2(
        Path(__file__).resolve(), server_cwd / "not_in_the_workspace.yaml"
    )

    # Act
    switched = _switch(client, workspace, "not_in_the_workspace.yaml")

    # Assert
    assert switched.status_code == 404, switched.content


# ---------------------------------------------------------------------------
# The first figure
# ---------------------------------------------------------------------------


def test_an_empty_workspace_is_seeded_with_a_recipe(client, split_workspace):
    # Arrange
    workspace, _ = split_workspace

    # Act
    body = _seed_demo(client, workspace)

    # Assert
    assert (workspace / body["recipe_path"]).is_file()


def test_seeding_an_empty_workspace_reports_that_it_wrote(
    client, split_workspace
):
    # Arrange
    workspace, _ = split_workspace

    # Act
    body = _seed_demo(client, workspace)

    # Assert
    assert body["seeded"] is True


def test_the_seeded_figure_actually_renders(client, split_workspace):
    # Arrange
    workspace, _ = split_workspace
    recipe_path = _seed_demo(client, workspace)["recipe_path"]

    # Act — the same call the canvas makes to draw it
    switched = _switch(client, workspace, recipe_path)

    # Assert
    assert json.loads(switched.content).get("image"), switched.content[:400]


def test_the_seeded_figure_carries_data_for_the_table_pane(
    client, split_workspace
):
    """"No tables" was the other half of the empty first screen."""
    # Arrange
    workspace, _ = split_workspace
    recipe_path = _seed_demo(client, workspace)["recipe_path"]

    # Act
    csvs = sorted((workspace / f"{Path(recipe_path).stem}_data").glob("*.csv"))

    # Assert
    assert csvs, "the seeded figure shipped no data for the table pane"


def test_reseeding_returns_the_same_recipe(client, split_workspace):
    # Arrange
    workspace, _ = split_workspace
    first = _seed_demo(client, workspace)

    # Act
    second = _seed_demo(client, workspace)

    # Assert
    assert second["recipe_path"] == first["recipe_path"]


def test_reseeding_never_overwrites_the_users_edits(client, split_workspace):
    # Arrange
    workspace, _ = split_workspace
    recipe = workspace / _seed_demo(client, workspace)["recipe_path"]
    recipe.write_text(recipe.read_text() + "\n# edited by the user\n")
    edited = recipe.read_text()

    # Act
    _seed_demo(client, workspace)

    # Assert
    assert recipe.read_text() == edited


def test_a_workspace_with_its_own_recipes_is_not_seeded(
    client, split_workspace
):
    # Arrange — a project that already has work in it
    workspace, _ = split_workspace
    _post(client, "api/gallery/add", workspace, {"template": "plot_scatter"})

    # Act
    body = _seed_demo(client, workspace)

    # Assert
    assert body["recipe_path"] is None


def test_a_workspace_with_its_own_recipes_is_not_littered(
    client, split_workspace
):
    # Arrange
    workspace, _ = split_workspace
    _post(client, "api/gallery/add", workspace, {"template": "plot_scatter"})

    # Act
    _seed_demo(client, workspace)

    # Assert
    assert not list(workspace.glob("demo_first_figure*"))


def test_an_unwritable_workspace_degrades_instead_of_erroring(
    client, locked_workspace
):
    """A missing first impression is a disappointment, never an outage."""
    # Arrange
    endpoint = "api/gallery/demo"

    # Act
    response = _post(client, endpoint, locked_workspace, {})

    # Assert
    assert response.status_code == 200, response.content


def test_an_unwritable_workspace_reports_no_recipe(client, locked_workspace):
    # Arrange
    endpoint = "api/gallery/demo"

    # Act
    response = _post(client, endpoint, locked_workspace, {})

    # Assert
    assert json.loads(response.content)["recipe_path"] is None


# EOF
