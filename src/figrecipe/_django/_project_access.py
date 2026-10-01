"""Project capability checks owned by the editor, before any hosted file I/O.

Standalone settings explicitly opt into local paths. Every other mount fails
closed through the SDK host provider; process cwd and launch environment are
never authority for a hosted request.
"""

import json
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from scitex_sdk.host import AccessError, project_access

from ._local_files import LocalFilesAdapter

_READ_ENDPOINTS = {
    "ping",
    "preview",
    "hitmap",
    "style",
    "overrides",
    "theme",
    "list_themes",
    "diff",
    "get_labels",
    "get_axis_info",
    "get_legend_info",
    "get_axes_positions",
    "calls",
    "element_details",
    "get_captions",
    "datatable/data",
    "download/csv",
    "api/tree",
    "api/files",
    "api/download",
    "api/gallery",
    "stats/list_brackets",
    "api/switch",
}
_READ_PREFIXES = (
    "download/",
    "api/file-content/",
    "api/gallery/thumbnail/",
    "api/compose/export/",
)


def hub_mode():
    return getattr(settings, "SCITEX_APP_MODE", "hub") != "standalone"


def requires_write(request, endpoint):
    if endpoint is None or endpoint in _READ_ENDPOINTS:
        return False
    if endpoint.startswith(_READ_PREFIXES):
        return False
    if endpoint.startswith(("call/", "api/chat/sessions/")):
        return request.method not in ("GET", "HEAD", "OPTIONS")
    return True


def _path(access, value, base=None):
    if not isinstance(value, str) or "\x00" in value:
        raise AccessError("Invalid path", 400)
    try:
        return access.path((base or access.root) / value)
    except (AccessError, OSError, ValueError) as exc:
        raise AccessError("Path is outside the selected project", 403) from exc


def _body(request):
    try:
        data = json.loads(request.body) if request.body else {}
    except (ValueError, UnicodeDecodeError) as exc:
        raise AccessError("Invalid JSON body", 400) from exc
    if not isinstance(data, dict):
        raise AccessError("JSON body must be an object", 400)
    return data


def _relative(value):
    if not isinstance(value, str) or "\x00" in value:
        raise AccessError("Invalid package asset name", 400)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AccessError("Invalid package asset name", 403)


def prepare_request(request, endpoint=None):
    """Resolve authority, validate all input channels and normalize handler paths."""
    if not hub_mode():
        return
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        raise AccessError("Authentication required", 401)
    write = requires_write(request, endpoint)
    # Resource requests retain their explicit authority without changing the
    # selected navigation project when an older request completes late.
    access = project_access(request, write=write, remember=endpoint is None)
    data = _body(request)
    query = request.GET.copy()
    # Validate even duplicate/unused selectors: none may bypass the boundary.
    for value in query.getlist("working_dir"):
        _path(access, value)
    if "working_dir" in data:
        _path(access, data["working_dir"])
    working_dir = _path(access, query.get("working_dir") or "")
    request._figrecipe_project = access
    request._figrecipe_working_dir = working_dir
    for key in ("path", "recipe", "recipe_path"):
        for value in query.getlist(key):
            _path(access, value, working_dir)
        if key != "path" and key in query and query[key]:
            query[key] = str(_path(access, query[key], working_dir))
        if key in data:
            value = _path(access, data[key], working_dir)
            if key != "path":
                data[key] = str(value) if data[key] else ""
    if endpoint and endpoint.startswith("api/file-content/"):
        _path(access, endpoint[len("api/file-content/") :], working_dir)
    if endpoint and endpoint.startswith("api/gallery/thumbnail/"):
        _relative(endpoint[len("api/gallery/thumbnail/") :])
    if endpoint in ("api/gallery/add", "api/gallery/demo"):
        from .handlers.gallery import DEMO_TEMPLATE_NAME, TEMPLATES_DIR

        name = (
            data.get("template", "")
            if endpoint.endswith("/add")
            else DEMO_TEMPLATE_NAME
        )
        _relative(name)
        source = (TEMPLATES_DIR / f"{name}.yaml").resolve()
        if not source.is_relative_to(TEMPLATES_DIR.resolve()):
            raise AccessError("Invalid package asset name", 403)
        check_output(request, working_dir / source.name)
        check_output(request, working_dir / f"{name}_data")
    if endpoint == "api/compose":
        name = data.get("filename", "composed")
        _relative(name)
        check_output(request, working_dir / f"{name}.png")
        # Compose has a separate body working_dir sink. Give it authority too.
        data["working_dir"] = str(working_dir)
    if endpoint == "add_image_from_url":
        url = data.get("url", "")
        if not isinstance(url, str) or urlparse(url).scheme.lower() not in (
            "http",
            "https",
        ):
            raise AccessError("Image URL must use HTTP or HTTPS", 403)
    if endpoint == "switch_theme" and data.get("theme"):
        from figrecipe.styles._style_loader import _PRESET_ALIASES, list_presets

        # load_preset joins an uppercased name onto its package directory.
        # Only advertised names are a theme selector in a hosted editor.
        name = data["theme"].upper() if isinstance(data["theme"], str) else ""
        if _PRESET_ALIASES.get(name, name) not in list_presets():
            raise AccessError("Unknown theme", 400)
    from ._project_recipe import validate_recipe

    for value in (query.get("recipe"), data.get("recipe_path")):
        if value:
            validate_recipe(access, Path(value))
    if endpoint == "api/switch" and data.get("path"):
        validate_recipe(access, _path(access, data["path"], working_dir))
    if endpoint == "load_recipe" and data.get("recipe_content"):
        from ruamel.yaml import YAML
        from ruamel.yaml.error import YAMLError

        from ._project_recipe import validate_data

        try:
            content = YAML(typ="safe").load(data["recipe_content"])
        except (YAMLError, TypeError) as exc:
            raise AccessError("Invalid recipe YAML", 400) from exc
        validate_data(access, content, working_dir)
    query["working_dir"] = str(working_dir)
    request.GET = query
    if request.body:
        request._body = json.dumps(data).encode()
    # Mutation handlers cannot be reached through a CSRF-safe HTTP method.
    if write and request.method in ("GET", "HEAD", "OPTIONS"):
        raise AccessError("Use POST for this operation", 405)


class ProjectFiles(LocalFilesAdapter):
    """Local file protocol confined by the same SDK capability as direct I/O."""

    def __init__(self, access, root):
        super().__init__(root)
        self.access = access

    def _resolve(self, path):
        return _path(self.access, path, self._root)

    def list(self, directory="", *, extensions=None):
        entries = super().list(directory, extensions=extensions)
        contained = []
        for entry in entries:
            try:
                self._resolve(entry)
            except AccessError:
                continue
            contained.append(entry)
        return contained

    def list_entries(self, directory=""):
        # The shared tree builder otherwise inspects _root directly, bypassing
        # the capability's symlink checks. Its typed protocol avoids that path.
        return [
            {
                "path": entry,
                "type": "directory" if self._resolve(entry).is_dir() else "file",
            }
            for entry in self.list(directory)
        ]

    def _writable(self):
        if self.access.can_write is not True:
            raise AccessError("Write access required", 403)

    def write(self, path, content):
        self._writable()
        return super().write(path, content)

    def delete(self, path):
        self._writable()
        return super().delete(path)

    def rename(self, old_path, new_path):
        self._writable()
        return super().rename(old_path, new_path)

    def copy(self, src_path, dest_path):
        self._writable()
        return super().copy(src_path, dest_path)


def editor_key(request, path):
    access = getattr(request, "_figrecipe_project", None)
    if access is None:
        return f"figrecipe_{path}"
    user_id = str(getattr(request.user, "pk", ""))
    return repr(("figrecipe", user_id, access.id, str(access.root), str(path)))


def bind_editor(request, editor):
    access = getattr(request, "_figrecipe_project", None)
    if access is not None:
        editor.working_dir = request._figrecipe_working_dir
        editor._files_backend = ProjectFiles(access, editor.working_dir)
        if editor.recipe_path:
            from figrecipe._editor._overrides import get_overrides_path

            _path(access, str(editor.recipe_path))
            check_output(request, get_overrides_path(editor.recipe_path))
            check_output(
                request, editor.recipe_path.with_name(f"{editor.recipe_path.stem}_data")
            )


def check_output(request, path):
    """Preflight generated outputs too, including pre-existing symlink targets."""
    access = getattr(request, "_figrecipe_project", None)
    if access is None:
        return
    target = _path(access, str(path))
    if target.is_dir():
        for child in target.rglob("*"):
            _path(access, str(child))
