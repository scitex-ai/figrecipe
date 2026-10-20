"""Real project mutation and generated-target controls with isolated files."""

import base64
import io

import pytest

from .test_project_capability import (  # noqa: F401 - fixture registration
    hosted,
    in_directory,
    post,
)


def test_compose_without_caller_working_dir_writes_to_project(hosted):
    # Arrange
    contract = {}
    # Act
    from PIL import Image

    client, root = hosted
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
    with in_directory(root / "beta"):
        response = post(client, "api/compose", body)
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    contract["2: (root / 'alpha/composed.png').exists()"] = bool(
        (root / "alpha/composed.png").exists()
    )
    contract["3: not (root / 'beta/composed.png').exists()"] = bool(
        not (root / "beta/composed.png").exists()
    )
    # Assert
    assert all(contract.values()), contract


def test_generated_compose_target_symlink_denied(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "alpha/composed.png").symlink_to(root / "beta/data.txt")
    contract["1: post(client, 'api/compose', {}).status_code == 403"] = bool(
        post(client, "api/compose", {}).status_code == 403
    )
    contract["2: (root / 'beta/data.txt').read_text() == 'beta'"] = bool(
        (root / "beta/data.txt").read_text() == "beta"
    )
    # Assert
    assert all(contract.values()), contract


def test_recipe_data_reference_checked_before_loader(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "alpha/bad.yaml").write_text(
        "figure: {}\naxes: {}\ndata:\n  csv_format: single\n  csv_path: ../beta/data.txt\n"
    )
    contract[
        "1: client.get('/apps/figrecipe/ping?recipe=bad.yaml').status_code == 403"
    ] = bool(client.get("/apps/figrecipe/ping?recipe=bad.yaml").status_code == 403)
    body = {
        "recipe_content": "axes:\n  ax_0_0:\n    subpanels:\n      - axes:\n          calls:\n            - args:\n                - data: ../beta/data.csv\n"
    }
    contract["2: post(client, 'load_recipe', body).status_code == 403"] = bool(
        post(client, "load_recipe", body).status_code == 403
    )
    # Assert
    assert all(contract.values()), contract


def test_hosted_create_edit_save_datatable_and_download(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    response = post(client, "api/new")
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    recipe = response.json()["file"]
    contract["2: (root / 'alpha' / recipe).exists()"] = bool(
        (root / "alpha" / recipe).exists()
    )
    contract[
        "3: client.get('/apps/figrecipe/preview', {'recipe': recipe}).status_code == 200"
    ] = bool(
        client.get("/apps/figrecipe/preview", {"recipe": recipe}).status_code == 200
    )
    response = post(client, f"save?recipe={recipe}", {"overrides": {}})
    contract["4: response.status_code == 200"] = bool(response.status_code == 200)
    contract["5: (root / 'alpha' / recipe).with_suffix('.overrides.json').exists()"] = (
        bool((root / "alpha" / recipe).with_suffix(".overrides.json").exists())
    )
    response = post(
        client, f"datatable/import?recipe={recipe}", {"content": "x,y\n1,2\n3,4\n"}
    )
    contract["6: response.status_code == 200"] = bool(response.status_code == 200)
    data = client.get("/apps/figrecipe/datatable/data", {"recipe": recipe}).json()
    contract["7: data['source'] == 'project'"] = bool(data["source"] == "project")
    contract["8: data['rows'] == [[1.0, 2.0], [3.0, 4.0]]"] = bool(
        data["rows"] == [[1.0, 2.0], [3.0, 4.0]]
    )
    response = client.get("/apps/figrecipe/api/download", {"recipe": recipe})
    contract["9: response.status_code == 200"] = bool(response.status_code == 200)
    contract["10: b'figure:' in b''.join(response.streaming_content)"] = bool(
        b"figure:" in b"".join(response.streaming_content)
    )
    # Assert
    assert all(contract.values()), contract


def test_loaded_editors_for_collaborators_are_distinct(hosted):
    # Arrange
    contract = {}
    # Act
    from figrecipe._django.services import _editor_cache

    client, _ = hosted
    recipe = post(client, "api/new").json()["file"]
    contract[
        "1: client.get('/apps/figrecipe/preview', {'recipe': recipe}).status_code == 200"
    ] = bool(
        client.get("/apps/figrecipe/preview", {"recipe": recipe}).status_code == 200
    )
    contract[
        "2: client.get('/apps/figrecipe/preview', {'recipe': recipe, 'project': 'alpha'}, HTTP_X_USER='bob').status_code == 200"
    ] = bool(
        client.get(
            "/apps/figrecipe/preview",
            {"recipe": recipe, "project": "alpha"},
            HTTP_X_USER="bob",
        ).status_code
        == 200
    )
    editors = [value[0] for key, value in _editor_cache.items() if recipe in key]
    contract["3: len(editors) == 2"] = bool(len(editors) == 2)
    contract["4: editors[0] is not editors[1]"] = bool(editors[0] is not editors[1])
    # Assert
    assert all(contract.values()), contract


def test_generated_new_figure_output_symlink_denied(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "alpha/new_figure_001.png").symlink_to(root / "beta/data.txt")
    contract["1: post(client, 'api/new').status_code == 403"] = bool(
        post(client, "api/new").status_code == 403
    )
    contract["2: (root / 'beta/data.txt').read_text() == 'beta'"] = bool(
        (root / "beta/data.txt").read_text() == "beta"
    )
    # Assert
    assert all(contract.values()), contract


def test_new_figure_checks_automatically_loaded_overrides_before_reproduction(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "alpha/new_figure_001.overrides.json").symlink_to(root / "beta/data.txt")
    contract["1: post(client, 'api/new').status_code == 403"] = bool(
        post(client, "api/new").status_code == 403
    )
    contract["2: not (root / 'alpha/new_figure_001.yaml').exists()"] = bool(
        not (root / "alpha/new_figure_001.yaml").exists()
    )
    # Assert
    assert all(contract.values()), contract


def test_demo_scan_ignores_recipes_outside_project(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "beta/other.yaml").write_text("figure: {}\naxes: {}\n")
    (root / "alpha/linked.yaml").symlink_to(root / "beta/other.yaml")
    response = post(client, "api/gallery/demo")
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    contract["2: response.json()['seeded'] is True"] = bool(
        response.json()["seeded"] is True
    )
    contract["3: (root / 'alpha' / response.json()['recipe_path']).exists()"] = bool(
        (root / "alpha" / response.json()["recipe_path"]).exists()
    )
    switched = post(client, "api/switch", {"path": response.json()["recipe_path"]})
    contract["4: switched.status_code == 200"] = bool(switched.status_code == 200)
    contract["5: switched.json()['image']"] = bool(switched.json()["image"])
    # Assert
    assert all(contract.values()), contract


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


def test_hosted_stats_import_uses_selected_project(hosted):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    with in_directory(root / "beta"):
        response = post(
            client,
            "api/import/stats-plot-spec",
            {"spec": correlation_spec(), "name": "stats"},
        )
    contract["1: response.status_code == 200"] = bool(response.status_code == 200)
    contract["2: (root / 'alpha/stats_001.yaml').exists()"] = bool(
        (root / "alpha/stats_001.yaml").exists()
    )
    contract["3: (root / 'alpha/stats_001.png').exists()"] = bool(
        (root / "alpha/stats_001.png").exists()
    )
    contract["4: not (root / 'beta/stats_001.yaml').exists()"] = bool(
        not (root / "beta/stats_001.yaml").exists()
    )
    # Assert
    assert all(contract.values()), contract


@pytest.mark.parametrize("output", ["stats_001.png", "stats_001.tex", "stats_001_data"])
def test_stats_import_generated_targets_cannot_escape_project(hosted, output):
    # Arrange
    contract = {}
    # Act
    client, root = hosted
    (root / "alpha" / output).symlink_to(root / "beta/data.txt")
    response = post(
        client,
        "api/import/stats-plot-spec",
        {"spec": correlation_spec(), "name": "stats"},
    )
    contract["1: response.status_code == 403"] = bool(response.status_code == 403)
    contract["2: (root / 'beta/data.txt').read_text() == 'beta'"] = bool(
        (root / "beta/data.txt").read_text() == "beta"
    )
    contract["3: not (root / 'alpha/stats_001.yaml').exists()"] = bool(
        not (root / "alpha/stats_001.yaml").exists()
    )
    # Assert
    assert all(contract.values()), contract


def test_hosted_zip_is_explicitly_unavailable(hosted):
    # Arrange
    client, root = hosted
    (root / "alpha/recipe.zip").write_bytes(b"fixture")
    # Act
    # Assert
    assert client.get("/apps/figrecipe/ping?recipe=recipe.zip").status_code == 501
