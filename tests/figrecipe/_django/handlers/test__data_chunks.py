"""Data identities follow actual recorded YAML/CSV/NPY provenance."""
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")

@pytest.fixture(scope="module", autouse=True)
def django_ready():
    import django
    django.setup()


def test_real_gallery_csv_recipe_exposes_actual_sources():
    import figrecipe as fr
    from figrecipe._django.services import EditorState
    from figrecipe._django.handlers.datatable import handle_datatable_data
    # Arrange
    recipe = Path(fr.__file__).parent / "_django/gallery_templates/plot_plot.yaml"
    fig, _ = fr.reproduce(recipe)
    try:
        # Act
        payload = json.loads(handle_datatable_data(None, EditorState(fig=fig, recipe_path=recipe)).content)
        chunks = payload["chunks"]
        # Assert
        assert (bool(chunks), {chunk["kind"] for chunk in chunks},
                all(chunk["source_ref"].endswith(".csv") for chunk in chunks),
                {chunk["panel_path"] for chunk in chunks},
                sum(len(chunk["columns"]) for chunk in chunks),
                {len(chunk["rows"]) for chunk in chunks}) == (
                    True, {"linked"}, True, {str(recipe)}, len(payload["columns"]), {100}
                )
    finally:
        import matplotlib.pyplot as plt
        plt.close(fig.fig)


def test_inline_yaml_and_linked_npy_are_distinct_without_reading_guessed_files(tmp_path):
    from figrecipe._django.handlers._data_chunks import table_chunks
    # Arrange
    call = NS(id="line", args=[{"data":[1,2]}, {"data":[3,4], "_source_file":str(tmp_path / "measurements.npy")}], kwargs={})
    editor = NS(recipe_path=tmp_path / "panel.yaml", fig=NS(record=NS(axes={"ax":NS(calls=[call])})))
    # Act
    chunks = table_chunks(editor, ["line_x","line_y"], [[1,3],[2,4]], "record", None)
    # Assert
    assert [(c["kind"], c["label"], c["rows"], c["source"]) for c in chunks] == [
        ("inline", "panel.yaml · inline", [[1], [2]], "record"),
        ("linked", "measurements.npy", [[3], [4]], "record")
    ]


def test_project_owned_table_names_its_actual_csv_and_revision(tmp_path):
    from figrecipe._django.handlers._data_chunks import table_chunks
    # Arrange
    editor = NS(recipe_path=tmp_path / "panel.yaml", working_dir=tmp_path)
    # Act
    chunks = table_chunks(editor, ["signal"], [[42]], "project", "r42")
    # Assert
    assert [(c["label"], c["revision"]) for c in chunks] == [("panel_data.csv", "r42")]


def test_nested_recipe_file_list_preserves_canonical_identity(tmp_path):
    import shutil
    import figrecipe as fr
    from django.test import RequestFactory
    from figrecipe._django.services import EditorState
    from figrecipe._django.handlers.files import handle_api_files
    # Arrange
    nested = tmp_path / "nested" / "panel.yaml"
    nested.parent.mkdir()
    shutil.copyfile(Path(fr.__file__).parent / "_django/gallery_templates/plot_plot.yaml", nested)
    editor = EditorState(recipe_path=nested, working_dir=tmp_path)
    request = RequestFactory().get("/api/files", {"working_dir":str(tmp_path)})
    # Act
    payload = json.loads(handle_api_files(request, editor).content)
    # Assert
    assert (payload["recipe_path"], payload["current_file"]) == (str(nested), "panel.yaml")
