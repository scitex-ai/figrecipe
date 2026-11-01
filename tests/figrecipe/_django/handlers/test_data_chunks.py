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
    recipe = Path(fr.__file__).parent / "_django/gallery_templates/plot_plot.yaml"
    fig, _ = fr.reproduce(recipe)
    try:
        payload = json.loads(handle_datatable_data(None, EditorState(fig=fig, recipe_path=recipe)).content)
        chunks = payload["chunks"]
        assert chunks and all(chunk["kind"] == "linked" for chunk in chunks)
        assert all(chunk["source_ref"].endswith(".csv") for chunk in chunks)
        assert all(chunk["panel_path"] == str(recipe) for chunk in chunks)
        assert sum(len(chunk["columns"]) for chunk in chunks) == len(payload["columns"])
        assert all(len(chunk["rows"]) == 100 for chunk in chunks)
    finally:
        import matplotlib.pyplot as plt
        plt.close(fig.fig)


def test_inline_yaml_and_linked_npy_are_distinct_without_reading_guessed_files(tmp_path):
    from figrecipe._django.handlers._data_chunks import table_chunks
    call = NS(id="line", args=[{"data":[1,2]}, {"data":[3,4], "_source_file":str(tmp_path / "measurements.npy")}], kwargs={})
    editor = NS(recipe_path=tmp_path / "panel.yaml", fig=NS(record=NS(axes={"ax":NS(calls=[call])})))
    chunks = table_chunks(editor, ["line_x","line_y"], [[1,3],[2,4]], "record", None)
    assert [chunk["kind"] for chunk in chunks] == ["inline","linked"]
    assert [chunk["label"] for chunk in chunks] == ["panel.yaml · inline","measurements.npy"]
    assert [chunk["rows"] for chunk in chunks] == [[[1],[2]],[[3],[4]]]
    assert all(chunk["source"] == "record" for chunk in chunks)


def test_project_owned_table_names_its_actual_csv_and_revision(tmp_path):
    from figrecipe._django.handlers._data_chunks import table_chunks
    editor = NS(recipe_path=tmp_path / "panel.yaml", working_dir=tmp_path)
    chunks = table_chunks(editor, ["signal"], [[42]], "project", "r42")
    assert len(chunks) == 1
    assert chunks[0]["label"] == "panel_data.csv"
    assert chunks[0]["revision"] == "r42"


def test_nested_recipe_file_list_preserves_canonical_identity(tmp_path):
    import shutil
    import figrecipe as fr
    from django.test import RequestFactory
    from figrecipe._django.services import EditorState
    from figrecipe._django.handlers.files import handle_api_files
    nested = tmp_path / "nested" / "panel.yaml"
    nested.parent.mkdir()
    shutil.copyfile(Path(fr.__file__).parent / "_django/gallery_templates/plot_plot.yaml", nested)
    editor = EditorState(recipe_path=nested, working_dir=tmp_path)
    request = RequestFactory().get("/api/files", {"working_dir":str(tmp_path)})
    payload = json.loads(handle_api_files(request, editor).content)
    assert payload["recipe_path"] == str(nested)
    assert payload["current_file"] == "panel.yaml"
