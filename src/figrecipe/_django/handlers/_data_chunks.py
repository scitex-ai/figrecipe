"""Data chunks derive from recorded argument provenance, never tab position."""
from pathlib import Path


def table_chunks(editor, names, rows, source, revision):
    recipe = str(getattr(editor, "recipe_path", None) or "")
    recipe_name = Path(recipe).name or "figure.yaml"
    groups = {}

    def add(reference, kind, column):
        key = (reference, kind)
        if key not in groups:
            groups[key] = []
        if column in names and column not in groups[key]:
            groups[key].append(column)

    if source == "record":
        record = getattr(getattr(editor, "fig", None), "record", None)
        for axis in getattr(record, "axes", {}).values():
            for call in getattr(axis, "calls", []):
                cid = getattr(call, "call_id", None) or getattr(call, "id", None) or getattr(call, "function", "")
                args, kwargs = getattr(call, "args", []), getattr(call, "kwargs", {})
                for index, role in enumerate(("x", "y")):
                    argument = kwargs.get(role)
                    if argument is None and len(args) > index:
                        argument = args[index]
                    reference = argument.get("_source_file") if isinstance(argument, dict) else None
                    # Reproduced CSV/NPY arguments retain _source_file; inline
                    # arrays deliberately name the YAML, never a guessed CSV.
                    add(str(reference or recipe_name), "linked" if reference else "inline", f"{cid}_{role}")
    elif source in ("project", "import"):
        from .._project_table import project_table_path
        path = project_table_path(getattr(editor, "recipe_path", None), getattr(editor, "working_dir", None))
        for name in names:
            add(str(path or "Imported data"), source, name)

    chunks = []
    for (reference, kind), columns in groups.items():
        if not columns:
            continue
        indices = [names.index(name) for name in columns]
        basename = Path(reference).name
        chunks.append({
            "id": f"{recipe}::{kind}::{reference}",
            "label": f"{basename} · inline" if kind == "inline" else basename,
            "kind": kind, "panel_path": recipe, "source_ref": reference,
            "columns": [{"name": name} for name in columns],
            "rows": [[row[i] if i < len(row) else None for i in indices] for row in rows],
            "source": source, "revision": revision,
        })
    return chunks
