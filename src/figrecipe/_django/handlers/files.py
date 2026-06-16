#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File management handlers: list/switch/new/delete/rename/duplicate/download."""

import json
import logging
from pathlib import Path

from django.http import FileResponse, JsonResponse

logger = logging.getLogger(__name__)

# Directory-listing helpers extracted to _files_tree.py (tree enrichment,
# recipe detection, working-dir/backend resolution).
from ._core import _dpi_from_request  # noqa: E402
from ._files_tree import (  # noqa: E402
    _enrich_tree,
    _find_default_working_dir,
    _get_working_dir_and_backend,
    _is_figrecipe_yaml,
    _is_figrecipe_yaml_rel,
    _local_build_tree,
)

__all__ = [
    "_enrich_tree",
    "_find_default_working_dir",
    "_get_working_dir_and_backend",
    "_is_figrecipe_yaml",
    "_is_figrecipe_yaml_rel",
    "_local_build_tree",
]


def handle_api_tree(request, editor):
    """List ALL files in working dir as a tree (no filtering)."""
    try:
        from scitex_app import build_tree as _build_tree
    except ImportError:
        _build_tree = _local_build_tree

    working_dir, files_backend = _get_working_dir_and_backend(request, editor)
    max_depth = int(request.GET.get("depth", "2"))
    try:
        tree = _build_tree(files_backend, max_depth=max_depth)
    except PermissionError as exc:
        logger.warning("[api_tree] Permission denied: %s", exc)
        return JsonResponse(
            {
                "tree": [],
                "working_dir": str(working_dir),
                "error": f"Permission denied: {exc}",
            },
        )
    return JsonResponse({"tree": tree, "working_dir": str(working_dir)})


def handle_api_files(request, editor):
    """List recipe files in working dir as tree + flat list."""
    try:
        from scitex_app import build_tree as _build_tree
    except ImportError:
        _build_tree = _local_build_tree

    working_dir, files_backend = _get_working_dir_and_backend(request, editor)
    try:
        tree = _build_tree(files_backend, extensions=[".yaml", ".yml"])
        tree = _enrich_tree(tree, working_dir, editor, files_backend)
    except PermissionError:
        return JsonResponse({"tree": [], "files": [], "working_dir": str(working_dir)})

    flat_files = []

    def flatten(items):
        for item in items:
            if item["type"] == "directory":
                flatten(item.get("children", []))
            else:
                flat_files.append(item)

    flatten(tree)
    return JsonResponse(
        {
            "tree": tree,
            "files": flat_files,
            "working_dir": str(working_dir),
            "current_file": (
                str(editor.recipe_path.name)
                if editor and getattr(editor, "recipe_path", None)
                else None
            ),
        }
    )


def handle_api_switch(request, editor):
    """Switch to a different recipe file, or bootstrap editor on first load."""
    from figrecipe._editor._helpers import render_with_overrides
    from figrecipe._reproducer import reproduce

    data = json.loads(request.body) if request.body else {}
    file_path = data.get("path")
    if not file_path:
        return JsonResponse({"error": "No file path provided"}, status=400)

    # Resolve working_dir — use editor's if available, else default
    working_dir = getattr(editor, "working_dir", None) if editor else None
    wd_param = request.GET.get("working_dir")
    if wd_param:
        wd_path = Path(wd_param)
        if wd_path.is_dir():
            working_dir = wd_path
    if working_dir is None:
        working_dir = _find_default_working_dir()
    full_path = working_dir / file_path
    if not full_path.exists():
        # Try as absolute path
        full_path = Path(file_path)
    if not full_path.exists():
        return JsonResponse({"error": f"File not found: {file_path}"}, status=404)

    # Bootstrap editor if none exists (first file click)
    if editor is None:
        from ..services import get_or_create_editor

        session_key = f"figrecipe_{full_path}"
        editor = get_or_create_editor(session_key, str(full_path))

    # Sync dark_mode from frontend if provided
    req_dark = data.get("dark_mode")
    if req_dark is not None:
        editor.dark_mode = bool(req_dark)

    try:
        fig, _ = reproduce(full_path)
        editor.fig = fig
        editor.recipe_path = full_path
        editor._hitmap_generated = False
        editor._color_map = {}
        editor._overrides = None  # reset overrides; lazy rebuild from style

        img, bboxes, size = render_with_overrides(
            editor.fig,
            editor.get_effective_style(),
            editor.dark_mode,
            dpi=_dpi_from_request(request),
        )
        editor._hitmap_generated = False
        editor._color_map = {}

        return JsonResponse(
            {
                "success": True,
                "image": img,
                "bboxes": bboxes,
                "color_map": {},
                "img_size": {"width": size[0], "height": size[1]},
                "file": file_path,
                "working_dir": str(getattr(editor, "working_dir", full_path.parent)),
            }
        )
    except Exception as e:
        logger.exception("[FigRecipe] api_switch failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_api_new(request, editor):
    """Create a new blank figure file."""
    from figrecipe import reproduce, save, subplots
    from figrecipe._editor._helpers import render_with_overrides

    try:
        fig, ax = subplots()
        ax.set_title("New Figure")

        working_dir = getattr(editor, "working_dir", Path.cwd())
        files = editor.files
        counter = 1
        while True:
            rel_path = f"new_figure_{counter:03d}.yaml"
            if not files.exists(rel_path):
                break
            counter += 1
        file_path = working_dir / rel_path

        save(fig, file_path.with_suffix(".png"), validate=False, verbose=False)
        reproduced_fig, _ = reproduce(file_path)

        editor.fig = reproduced_fig
        editor.recipe_path = file_path
        editor._hitmap_generated = False
        editor._color_map = {}
        editor._overrides = None  # reset overrides; lazy rebuild from style

        img, bboxes, size = render_with_overrides(
            editor.fig,
            editor.get_effective_style(),
            editor.dark_mode,
            dpi=_dpi_from_request(request),
        )
        editor._hitmap_generated = False
        editor._color_map = {}

        return JsonResponse(
            {
                "success": True,
                "image": img,
                "bboxes": bboxes,
                "color_map": {},
                "img_size": {"width": size[0], "height": size[1]},
                "file": str(file_path.relative_to(working_dir)),
                "file_name": file_path.stem,
            }
        )
    except Exception as e:
        logger.exception("[FigRecipe] api_new failed")
        return JsonResponse({"error": str(e)}, status=500)


def handle_api_delete(request, editor):
    """Delete a recipe file and associated files."""
    data = json.loads(request.body) if request.body else {}
    file_path = data.get("path")
    if not file_path:
        return JsonResponse({"error": "No file path provided"}, status=400)

    working_dir = getattr(editor, "working_dir", Path.cwd())
    full_path = working_dir / file_path
    if full_path.suffix.lower() not in (".yaml", ".yml", ".png"):
        return JsonResponse({"error": "Invalid file type"}, status=400)

    base_name = Path(file_path).with_suffix("").as_posix()
    is_current = bool(
        editor.recipe_path
        and full_path.with_suffix("") == editor.recipe_path.with_suffix("")
    )
    deleted_files, errors = [], []
    files = editor.files

    for ext in [".yaml", ".yml", ".png", ".overrides.yaml"]:
        rel = f"{base_name}{ext}"
        if files.exists(rel):
            try:
                files.delete(rel)
                deleted_files.append(Path(rel).name)
            except Exception as e:
                errors.append(f"{Path(rel).name}: {e}")

    if not deleted_files:
        return JsonResponse({"error": "No files found to delete"}, status=404)

    switch_to = None
    if is_current:
        for f in files.list("", extensions=[".yaml"]):
            fname = Path(f).name
            if not fname.startswith(".") and not fname.endswith(".overrides.yaml"):
                switch_to = f
                break

    return JsonResponse(
        {
            "success": True,
            "deleted": deleted_files,
            "errors": errors or None,
            "was_current": is_current,
            "switch_to": switch_to,
        }
    )


def handle_api_rename(request, editor):
    """Rename a recipe file."""
    data = json.loads(request.body) if request.body else {}
    old_path = data.get("path")
    new_name = data.get("new_name")

    if not old_path:
        return JsonResponse({"error": "No file path provided"}, status=400)
    if not new_name:
        return JsonResponse({"error": "No new name provided"}, status=400)

    new_name = Path(new_name).stem
    if not new_name or "/" in new_name or "\\" in new_name:
        return JsonResponse({"error": "Invalid new name"}, status=400)

    working_dir = getattr(editor, "working_dir", Path.cwd())
    full_path = working_dir / old_path
    if full_path.suffix.lower() not in (".yaml", ".yml", ".png"):
        return JsonResponse({"error": "Invalid file type"}, status=400)

    old_base = Path(old_path).with_suffix("").as_posix()
    files = editor.files

    for ext in [".yaml", ".png"]:
        if files.exists(f"{new_name}{ext}"):
            return JsonResponse(
                {"error": f"File {new_name}{ext} already exists"}, status=400
            )

    renamed_files, errors = [], []
    for ext in [".yaml", ".yml", ".png", ".overrides.yaml"]:
        old_rel = f"{old_base}{ext}"
        new_rel = f"{new_name}{ext}"
        if files.exists(old_rel):
            try:
                files.rename(old_rel, new_rel)
                renamed_files.append(
                    {"from": Path(old_rel).name, "to": Path(new_rel).name}
                )
            except Exception as e:
                errors.append(f"{Path(old_rel).name}: {e}")

    if not renamed_files:
        return JsonResponse({"error": "No files found to rename"}, status=404)

    if editor.recipe_path and full_path.with_suffix(
        ""
    ) == editor.recipe_path.with_suffix(""):
        editor.recipe_path = working_dir / f"{new_name}.yaml"

    return JsonResponse(
        {
            "success": True,
            "renamed": renamed_files,
            "new_name": new_name,
            "errors": errors or None,
        }
    )


def handle_api_duplicate(request, editor):
    """Duplicate a recipe file."""
    data = json.loads(request.body) if request.body else {}
    file_path = data.get("path")
    if not file_path:
        return JsonResponse({"error": "No file path provided"}, status=400)

    working_dir = getattr(editor, "working_dir", Path.cwd())
    full_path = working_dir / file_path
    if full_path.suffix.lower() not in (".yaml", ".yml", ".png"):
        return JsonResponse({"error": "Invalid file type"}, status=400)

    base_name = Path(file_path).with_suffix("").as_posix()
    original_name = Path(file_path).stem
    files = editor.files

    counter = 1
    while True:
        new_name = f"{original_name}_copy_{counter:02d}"
        if not files.exists(f"{new_name}.yaml"):
            break
        counter += 1

    copied_files, errors = [], []
    for ext in [".yaml", ".yml", ".png", ".overrides.yaml"]:
        old_rel = f"{base_name}{ext}"
        new_rel = f"{new_name}{ext}"
        if files.exists(old_rel):
            try:
                files.copy(old_rel, new_rel)
                copied_files.append(
                    {"from": Path(old_rel).name, "to": Path(new_rel).name}
                )
            except Exception as e:
                errors.append(f"{Path(old_rel).name}: {e}")

    if not copied_files:
        return JsonResponse({"error": "No files found to duplicate"}, status=404)

    return JsonResponse(
        {
            "success": True,
            "copied": copied_files,
            "new_name": new_name,
            "new_path": f"{new_name}.yaml",
            "errors": errors or None,
        }
    )


def handle_api_download_recipe(request, editor):
    """Download the current recipe YAML file."""
    import io

    file_path_str = request.GET.get("path", "")
    if not file_path_str and editor.recipe_path:
        rel_path = str(editor.recipe_path.name)
    elif file_path_str:
        rel_path = file_path_str
        if not rel_path.endswith((".yaml", ".yml")):
            rel_path += ".yaml"
    else:
        return JsonResponse({"error": "No file path provided"}, status=400)

    files = editor.files
    if not files.exists(rel_path):
        return JsonResponse({"error": "File not found"}, status=404)

    content = files.read(rel_path, binary=True)
    return FileResponse(
        io.BytesIO(content),
        as_attachment=True,
        filename=Path(rel_path).name,
        content_type="application/x-yaml",
    )


def handle_api_file_content(request, editor, file_path):
    """Serve raw file content for Viewer pane (image, text, etc.)."""
    import mimetypes

    working_dir = _find_default_working_dir()
    full_path = (working_dir / file_path).resolve()
    # Path traversal protection
    if not str(full_path).startswith(str(working_dir.resolve())):
        return JsonResponse({"error": "Access denied"}, status=403)
    if not full_path.exists():
        return JsonResponse({"error": "File not found"}, status=404)

    raw = request.GET.get("raw") == "true"
    mime, _ = mimetypes.guess_type(str(full_path))

    if raw or (mime and mime.startswith("image")):
        return FileResponse(
            open(full_path, "rb"), content_type=mime or "application/octet-stream"
        )

    # Text content as JSON
    try:
        text = full_path.read_text(errors="replace")[:1_000_000]
        return JsonResponse({"content": text})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
