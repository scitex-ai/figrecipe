#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Directory-listing helpers for the file handlers.

Tree enrichment (recipe-file filtering + has_image/is_current flags), recipe
detection, and working-dir/backend resolution — the self-contained unit shared
by ``handle_api_tree`` / ``handle_api_files``. Extracted from ``files.py`` to
keep that handler module focused and under the line limit.
"""

from pathlib import Path


def _enrich_tree(tree, working_dir, editor, files_backend):
    """Add figrecipe-specific metadata to a generic file tree.

    Filters to recipe files only (must contain figure: and axes:),
    and adds has_image and is_current flags.
    """
    enriched = []
    for item in tree:
        if item["type"] == "directory":
            children = _enrich_tree(
                item.get("children", []), working_dir, editor, files_backend
            )
            if children:
                enriched.append({**item, "children": children})
        else:
            # Skip non-recipe files and overrides
            name = item["name"]
            if name.endswith(".overrides.yaml") or name == "__pycache__":
                continue
            rel_path = item["path"]
            full_path = working_dir / rel_path
            # Use relative path for backend reads, absolute for fallback
            if not _is_figrecipe_yaml_rel(rel_path, files_backend):
                continue
            png_path = Path(rel_path).with_suffix(".png").as_posix()
            enriched.append(
                {
                    **item,
                    "has_image": files_backend.exists(png_path),
                    "is_current": bool(
                        editor
                        and getattr(editor, "recipe_path", None)
                        and full_path.resolve() == editor.recipe_path.resolve()
                    ),
                }
            )
    return enriched


def _find_default_working_dir():
    """Find the working directory — respects FIGRECIPE_WORKING_DIR env var."""
    import os

    env_dir = os.environ.get("FIGRECIPE_WORKING_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p
    return Path.cwd()


# A file the backend refuses to read is simply "not a recipe" -- never a
# server error. scitex-app's FileSystemBackend raises ValueError("Path
# traversal detected") when a listed path resolves outside the root (e.g. a
# symlinked node_modules/@scitex/ui -> ../../scitex-ui in the figrecipe source
# tree). Without ValueError here, that single unreadable entry propagated out
# of the per-file recipe check and 500'd the whole /api/files tree.
_UNREADABLE = (OSError, UnicodeDecodeError, FileNotFoundError, ValueError)


def _is_figrecipe_yaml(path: Path, files_backend=None) -> bool:
    """Check if a YAML file is a figrecipe recipe (has figure: and axes: keys)."""
    try:
        if files_backend is not None:
            text = files_backend.read(str(path))[:2048]
        else:
            text = path.read_text(errors="ignore")[:2048]
        return "figure:" in text and "axes:" in text
    except _UNREADABLE:
        return False


def _is_figrecipe_yaml_rel(rel_path: str, files_backend) -> bool:
    """Check if a YAML file is a figrecipe recipe using a relative path."""
    try:
        text = files_backend.read(rel_path)[:2048]
        return "figure:" in text and "axes:" in text
    except _UNREADABLE:
        return False


def _local_build_tree(files_backend, extensions=None):
    """Fallback tree builder when scitex-app is not installed."""
    tree = []
    for f in files_backend.list("", extensions=extensions or []):
        tree.append({"name": Path(f).name, "path": f, "type": "file"})
    return tree


def _get_working_dir_and_backend(request, editor):
    """Resolve working directory and files backend from request context."""
    working_dir = getattr(editor, "working_dir", None) if editor else None
    wd_param = request.GET.get("working_dir")
    if wd_param:
        wd_path = Path(wd_param)
        if wd_path.is_dir():
            working_dir = wd_path
    if working_dir is None:
        working_dir = _find_default_working_dir()

    files_backend = editor.files if editor else None
    if files_backend is None:
        try:
            from scitex_app import get_files

            files_backend = get_files(root=str(working_dir))
        except ImportError:
            from .._local_files import LocalFilesAdapter

            files_backend = LocalFilesAdapter(working_dir)

    return working_dir, files_backend
