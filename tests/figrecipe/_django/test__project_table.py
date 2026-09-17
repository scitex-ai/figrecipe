#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The edited table is stored in the PROJECT, and only there.

Card figrecipe-data-column-and-plot-variant-ux-20260916 / scitex-hub PR 923
(Private Beta spec, FigRecipe slice): "project data, figure source, recipe, and
exported artifacts remain connected" and "never auto-select an unrelated example
project". The editor's table edits used to live only on the in-memory
EditorState (``imported_table``), so they vanished on restart and belonged to no
project; and ``EditorState.working_dir`` defaults to the server's CWD, which is
not a directory the user selected, so persisting there would attach the user's
data to an unrelated directory.

These tests pin the pure policy in ``figrecipe._django._project_table``: where
the table goes, what happens at each missing-project boundary, that the CSV
round-trips, and that the CWD never counts as a project. The handler wiring is
tested separately in ``tests/figrecipe/_django/handlers/``.

The file name mirrors the private module it covers (``_project_table.py`` ->
``test__project_table.py``), which is what the project-structure audit requires.

Each test makes a single assertion (STX-TQ007).
"""

from pathlib import Path

from figrecipe._django._project_table import (
    PROJECT_TABLE_SUFFIX,
    RECIPE_LESS_TABLE_NAME,
    is_selected_project_dir,
    is_within_project,
    load_project_table,
    project_table_path,
    read_table_csv,
    save_project_table,
    table_to_csv,
)

TABLE = (["mass", "label"], [[1.0, "a"], [2.0, "b"], [None, ""]])


class TestProjectTablePath:
    def test_recipe_table_sits_beside_the_recipe(self):
        # Arrange
        recipe = "/proj/twenty/plot.yaml"
        project = "/proj/twenty"
        # Act
        path = project_table_path(recipe, project)
        # Assert -- the project boundary is the RECIPE's directory, and the name
        # matches the CSV export's, so the stored and downloaded files read as
        # the same artifact.
        assert path == Path(f"/proj/twenty/plot{PROJECT_TABLE_SUFFIX}"), path

    def test_recipe_less_project_uses_the_figure_name(self):
        # Arrange -- an imported table in a project with no recipe yet.
        project = "/proj/twenty"
        # Act
        path = project_table_path(None, project)
        # Assert
        assert path == Path(f"/proj/twenty/{RECIPE_LESS_TABLE_NAME}"), path

    def test_no_recipe_and_no_working_dir_has_no_path(self):
        # Arrange
        recipe = None
        working_dir = None
        # Act
        path = project_table_path(recipe, working_dir)
        # Assert -- with nothing selected there is no project to attach the data
        # to; guessing one is the failure this prevents.
        assert path is None

    def test_a_stemless_recipe_has_no_path(self):
        # Arrange -- ``..yaml`` derives the stem "." and ``...yaml`` the stem
        # ".."; interpolating either would name a file OUTSIDE the project
        # (``../.._data.csv``).
        dotted_recipe = "/proj/..yaml"
        double_dotted_recipe = "/proj/...yaml"
        # Act
        dotted = project_table_path(dotted_recipe, "/proj")
        double_dotted = project_table_path(double_dotted_recipe, "/proj")
        # Assert
        assert (dotted, double_dotted) == (None, None), (dotted, double_dotted)


class TestSelectedProjectDir:
    def test_the_process_cwd_is_not_a_selected_project(self, tmp_path):
        # Arrange
        cwd = str(tmp_path)
        # Act
        result = is_selected_project_dir(cwd, cwd=cwd)
        # Assert -- the server's launch directory is not a directory anyone chose.
        assert result is False

    def test_a_different_directory_is_a_selected_project(self, tmp_path):
        # Arrange
        cwd = str(tmp_path)
        selected = "/some/where/project"
        # Act
        result = is_selected_project_dir(selected, cwd=cwd)
        # Assert
        assert result is True

    def test_a_missing_working_dir_is_not_a_project(self):
        # Arrange
        working_dir = None
        # Act
        result = is_selected_project_dir(working_dir)
        # Assert
        assert result is False


class TestWriteBoundary:
    def test_a_path_inside_the_project_is_accepted(self):
        # Arrange
        candidate = "/proj/twenty/data.csv"
        project = "/proj/twenty"
        # Act
        accepted = is_within_project(candidate, project)
        # Assert
        assert accepted is True

    def test_an_escaping_path_is_refused(self):
        # Arrange
        candidate = "/proj/other/data.csv"
        project = "/proj/twenty"
        # Act
        accepted = is_within_project(candidate, project)
        # Assert
        assert accepted is False


class TestCsvRoundTrip:
    def test_numbers_strings_and_empty_cells_survive(self):
        # Arrange
        names, rows = TABLE
        # Act
        back = read_table_csv(table_to_csv(names, rows))
        # Assert -- None became "" and comes back as ""; the numbers stay floats.
        assert back == (names, [[1.0, "a"], [2.0, "b"], ["", ""]]), back

    def test_text_that_is_not_a_table_is_rejected(self):
        # Arrange -- an empty file must not read as "a table with no rows".
        text = ""
        # Act
        parsed = read_table_csv(text)
        # Assert
        assert parsed is None

    def test_a_header_only_table_keeps_its_columns(self):
        # Arrange
        text = "mass,label\n"
        # Act
        parsed = read_table_csv(text)
        # Assert
        assert parsed == (["mass", "label"], []), parsed


class TestSaveAndLoad:
    def test_a_saved_table_comes_back_from_the_project(self, tmp_path):
        # Arrange
        recipe = tmp_path / "figure.yaml"
        recipe.write_text("recipe: {}\n", encoding="utf-8")
        names, rows = TABLE
        # Act
        save_project_table(recipe, None, names, rows)
        loaded = load_project_table(recipe, None)
        # Assert -- this is the restart case: a process that never saw the edit
        # reads it back from the project.
        assert loaded == (names, [[1.0, "a"], [2.0, "b"], ["", ""]]), loaded

    def test_saving_writes_inside_the_project_and_nowhere_else(self, tmp_path):
        # Arrange
        project = tmp_path / "twenty"
        project.mkdir()
        recipe = project / "figure.yaml"
        recipe.write_text("recipe: {}\n", encoding="utf-8")
        # Act
        written = save_project_table(recipe, None, *TABLE)
        outside = [path for path in tmp_path.iterdir() if path.is_file()]
        # Assert -- one new file, and it is the recipe's own table.
        assert written == project / f"figure{PROJECT_TABLE_SUFFIX}" and not outside

    def test_a_project_with_no_stored_table_loads_none(self, tmp_path):
        # Arrange
        recipe = tmp_path / "figure.yaml"
        recipe.write_text("recipe: {}\n", encoding="utf-8")
        # Act
        loaded = load_project_table(recipe, None)
        # Assert -- the pane then falls back to the figure's own data.
        assert loaded is None

    def test_nothing_is_written_without_a_project(self):
        # Arrange -- no recipe, no selected dir: refuse, do not guess.
        recipe = None
        working_dir = None
        # Act
        written = save_project_table(recipe, working_dir, *TABLE)
        # Assert
        assert written is None
