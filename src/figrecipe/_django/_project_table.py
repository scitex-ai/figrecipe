#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Data pane's table belongs to the PROJECT, not to the server process.

The editor's table edits (add/delete rows and columns, cell edits) are parsed by
``handle_datatable_import`` into ``editor.imported_table`` — an attribute on the
one EditorState object for that session. That is enough to survive a page
reload, and nothing more: restart the server (or open the same project in a
second process) and the edit is gone, because it was never written into the
project. The Private Beta spec's FigRecipe slice requires the opposite —
"project data, figure source, recipe, and exported artifacts remain connected"
(scitex-hub PR 923).

So an edited table is persisted next to the recipe that owns it, under the same
name the CSV export offers the user (``<recipe stem>_data.csv`` — see
``handlers/downloads.py``), and read back from there before anything else. Two
rules keep that honest:

* the file lives in the RECIPE'S directory (or the working dir when there is no
  recipe), which is the project boundary the hub establishes — never in the
  process CWD, which is unrelated to what the user selected; and
* a write that would escape that directory is refused, not sanitised: the path
  is derived rather than user-supplied, so an escaping path means something is
  wrong upstream and silently rewriting it would hide that.

Stdlib only and free of Django, so the path/CSV policy is unit-testable without
the app registry (``tests/figrecipe/_django/test_project_table.py``); the
handlers layer is tested separately against a real recipe.
"""

import csv
import io
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

import scitex_logging as slogging

logger = slogging.getLogger(__name__)

#: Same suffix the CSV export uses, so the file the user downloads and the file
#: the project keeps are recognisably the same artifact.
PROJECT_TABLE_SUFFIX = "_data.csv"

#: Used when the project has no recipe file (a brand-new project, just imported
#: data): the export falls back to this name too.
RECIPE_LESS_TABLE_NAME = "figure_data.csv"


def project_dir_for(
    recipe_path: Optional[Any] = None,
    working_dir: Optional[Any] = None,
) -> Optional[Path]:
    """The directory the table belongs to: the recipe's own, else the project's."""
    if recipe_path:
        try:
            return Path(recipe_path).expanduser().parent
        except (TypeError, ValueError):
            return None
    if working_dir:
        try:
            return Path(working_dir).expanduser()
        except (TypeError, ValueError):
            return None
    return None


def project_table_path(
    recipe_path: Optional[Any] = None,
    working_dir: Optional[Any] = None,
) -> Optional[Path]:
    """Where this project's edited table lives, or None when there is no project.

    ``None`` is the honest answer for a session with neither a recipe nor a
    working dir: there is no project to attach the data to, and writing into the
    process CWD would attach it to whatever directory the server was launched
    from.
    """
    project = project_dir_for(recipe_path, working_dir)
    if project is None:
        return None
    if not recipe_path:
        return project / RECIPE_LESS_TABLE_NAME
    stem = Path(recipe_path).stem
    # A stem of ""/"."/".." is not a name (a file called ".yaml" derives it);
    # interpolating it would produce a path for a different file.
    if stem in ("", ".", ".."):
        return None
    return project / f"{stem}{PROJECT_TABLE_SUFFIX}"


def is_selected_project_dir(working_dir: Any, cwd: Optional[Any] = None) -> bool:
    """Whether ``working_dir`` is a directory someone SELECTED, not the CWD.

    ``EditorState.working_dir`` defaults to ``Path.cwd()`` — the directory the
    server process happens to run in, which has no relationship to the project
    the user picked (it is the checkout the dev server was started from).
    Writing the user's table into it would attach project data to a directory
    nobody chose, which is the failure mode the Private Beta spec names: no
    silently created/selected project content. So persistence requires a
    working dir that is demonstrably a selection.
    """
    if not working_dir:
        return False
    try:
        here = Path(cwd) if cwd is not None else Path.cwd()
        return Path(working_dir).expanduser().resolve() != here.resolve()
    except (OSError, TypeError, ValueError):
        return False


def is_within_project(path: Any, project_dir: Any) -> bool:
    """Whether ``path`` sits inside ``project_dir`` (the write boundary)."""
    try:
        candidate = Path(path).resolve()
        root = Path(project_dir).resolve()
    except (OSError, TypeError, ValueError):
        return False
    return candidate == root or root in candidate.parents


def table_to_csv(names: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Serialise the table, empty cells preserved as empty fields."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(list(names))
    for row in rows:
        writer.writerow(["" if v is None else v for v in row])
    return buffer.getvalue()


def read_table_csv(text: str) -> Optional[Tuple[List[str], List[List[Any]]]]:
    """Parse a stored table; numeric cells come back as floats, as on import.

    Returns None for something that is not a table at all (no header line),
    rather than an empty table that would silently replace the user's data.
    """
    lines = list(csv.reader(io.StringIO(text)))
    if not lines:
        return None
    names = lines[0]
    rows: List[List[Any]] = []
    for line in lines[1:]:
        row: List[Any] = []
        for value in line:
            try:
                row.append(float(value))
            except ValueError:
                row.append(value)
        rows.append(row)
    return names, rows


def save_project_table(
    recipe_path: Optional[Any],
    working_dir: Optional[Any],
    names: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> Optional[Path]:
    """Write the edited table into the project; return the path, or None.

    Never raises: a table the project cannot store must not fail the edit the
    user already made in the pane (it stays live in ``imported_table``), so the
    reason is logged and the caller carries on.
    """
    path = project_table_path(recipe_path, working_dir)
    project = project_dir_for(recipe_path, working_dir)
    if path is None or project is None:
        logger.debug("[FigRecipe] No project to store the edited table in")
        return None
    if not is_within_project(path, project):
        logger.warning(
            "[FigRecipe] Refusing to store the edited table outside the "
            "project: %s not under %s",
            path,
            project,
        )
        return None
    try:
        project.mkdir(parents=True, exist_ok=True)
        path.write_text(table_to_csv(names, rows), encoding="utf-8")
        return path
    except OSError as exc:
        logger.warning("[FigRecipe] Could not store the edited table: %s", exc)
        return None


def load_project_table(
    recipe_path: Optional[Any],
    working_dir: Optional[Any],
) -> Optional[Tuple[List[str], List[List[Any]]]]:
    """The table this project has stored, or None when it has none."""
    path = project_table_path(recipe_path, working_dir)
    project = project_dir_for(recipe_path, working_dir)
    if path is None or project is None or not is_within_project(path, project):
        return None
    try:
        if not path.is_file():
            return None
        return read_table_csv(path.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.warning("[FigRecipe] Could not read the project table: %s", exc)
        return None


# EOF
