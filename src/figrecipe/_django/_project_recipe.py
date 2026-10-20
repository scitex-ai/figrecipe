"""Check recipe file references before the hosted editor's scientific loader."""

from scitex_sdk.host import AccessError


def validate_data(access, data, base):
    """Constrain serializer data references, including embedded subpanels."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and (
                key == "csv_path"
                or (key == "data" and value.endswith((".csv", ".npz", ".npy")))
            ):
                try:
                    access.path(base / value)
                except (AccessError, OSError, ValueError) as exc:
                    raise AccessError(
                        "Recipe data is outside the selected project", 403
                    ) from exc
            validate_data(access, value, base)
    elif isinstance(data, list):
        for item in data:
            validate_data(access, item, base)


def validate_recipe(access, path):
    if not path.exists():
        return  # The handler retains its normal missing-file response.
    # The core loader extracts ZIPs outside the workspace. Until it accepts a
    # confined extraction capability, keep this local-editor feature standalone.
    if path.suffix.lower() == ".zip":
        raise AccessError("ZIP recipes require the standalone editor", 501)
    from ruamel.yaml import YAML

    from figrecipe._utils._bundle import resolve_recipe_path

    try:
        resolved, _ = resolve_recipe_path(path)
    except (FileNotFoundError, ValueError):
        return
    try:
        resolved = access.path(resolved)
        # reproduce() automatically reads this sibling before the editor binds
        # its file backend, so validating it after loading would be too late.
        access.path(resolved.with_suffix(".overrides.json"))
    except (AccessError, OSError, ValueError) as exc:
        raise AccessError("Recipe is outside the selected project", 403) from exc
    from ruamel.yaml.error import YAMLError

    try:
        data = YAML(typ="safe").load(resolved.read_text())
    except (YAMLError, UnicodeDecodeError) as exc:
        raise AccessError("Invalid recipe YAML", 400) from exc
    validate_data(access, data, resolved.parent)
