#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python API introspection commands for figrecipe."""

import click

from ._json_output import json_requested

# Color mapping for types (matching scitex)
TYPE_COLORS = {"M": "blue", "C": "magenta", "F": "green", "V": "cyan"}


def _format_python_signature(
    func, multiline: bool = True, indent: str = "  "
) -> tuple[str, str]:
    """Format Python function signature with colors matching mcp list-tools.

    Returns (name_colored, signature_colored)
    """
    import inspect

    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return click.style(func.__name__, fg="green", bold=True), ""

    params = []
    for name, param in sig.parameters.items():
        # Get type annotation
        if param.annotation != inspect.Parameter.empty:
            ann = param.annotation
            type_str = ann.__name__ if hasattr(ann, "__name__") else str(ann)
            # Clean up complex type strings
            type_str = type_str.replace("typing.", "")
        else:
            type_str = None

        # Get default value
        if param.default != inspect.Parameter.empty:
            default = param.default
            def_str = repr(default) if len(repr(default)) < 20 else "..."
            if type_str:
                p = f"{click.style(name, fg='white', bold=True)}: {click.style(type_str, fg='cyan')} = {click.style(def_str, fg='yellow')}"
            else:
                p = f"{click.style(name, fg='white', bold=True)} = {click.style(def_str, fg='yellow')}"
        else:
            if type_str:
                p = f"{click.style(name, fg='white', bold=True)}: {click.style(type_str, fg='cyan')}"
            else:
                p = click.style(name, fg="white", bold=True)
        params.append(p)

    # Return type
    ret_str = ""
    if sig.return_annotation != inspect.Parameter.empty:
        ret = sig.return_annotation
        ret_name = ret.__name__ if hasattr(ret, "__name__") else str(ret)
        ret_name = ret_name.replace("typing.", "")
        ret_str = f" -> {click.style(ret_name, fg='magenta')}"

    name_s = click.style(func.__name__, fg="green", bold=True)

    if multiline and len(params) > 2:
        param_indent = indent + "    "
        params_str = ",\n".join(f"{param_indent}{p}" for p in params)
        sig_s = f"(\n{params_str}\n{indent}){ret_str}"
    else:
        sig_s = f"({', '.join(params)}){ret_str}"

    return name_s, sig_s


def _get_api_tree(module, max_depth: int = 5, docstring: bool = False):
    """Get API tree for a module with types and signatures.

    Returns list of dicts with: Name, Type, Depth, Docstring (optional)
    """
    import inspect

    results = []

    def _visit(obj, name: str, depth: int, visited: set):
        if depth > max_depth:
            return
        obj_id = id(obj)
        if obj_id in visited:
            return
        visited.add(obj_id)

        # Determine type
        if inspect.ismodule(obj):
            obj_type = "M"
        elif inspect.isclass(obj):
            obj_type = "C"
        elif callable(obj):
            obj_type = "F"
        else:
            obj_type = "V"

        entry = {"Name": name, "Type": obj_type, "Depth": depth}
        if docstring:
            entry["Docstring"] = inspect.getdoc(obj) or ""
        results.append(entry)

        # Recurse into modules and classes
        if inspect.ismodule(obj) and depth < max_depth:
            # Only visit items in __all__ if defined
            if hasattr(obj, "__all__"):
                members = [(n, getattr(obj, n, None)) for n in obj.__all__]
            else:
                members = [
                    (n, v) for n, v in inspect.getmembers(obj) if not n.startswith("_")
                ]
            for member_name, member_obj in members:
                if member_obj is not None:
                    _visit(member_obj, f"{name}.{member_name}", depth + 1, visited)

    _visit(module, module.__name__.split(".")[-1], 0, set())
    return results


@click.command("list-python-apis")
@click.option("-v", "--verbose", count=True, help="Verbosity: -v +doc, -vv full doc")
@click.option("-d", "--max-depth", type=int, default=5, help="Max recursion depth")
@click.option("--root-only", is_flag=True, help="Show only root-level items")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_python_apis(verbose: int, max_depth: int, root_only: bool, as_json: bool):
    """List Python APIs (figrecipe public API tree).

    Shows modules [M], classes [C], functions [F], and variables [V]
    with signatures and optional docstrings.

    \b
    Examples:
      figrecipe list-python-apis
      figrecipe list-python-apis -v
      figrecipe list-python-apis --json
    """

    as_json = json_requested(as_json)

    import figrecipe

    df = _get_api_tree(
        figrecipe, max_depth=max_depth if not root_only else 1, docstring=(verbose >= 1)
    )

    if as_json:
        import json

        click.echo(json.dumps(df, indent=2))
    else:
        click.secho(f"API tree of figrecipe ({len(df)} items):", fg="cyan")
        legend = " ".join(
            click.style(f"[{t}]={n}", fg=TYPE_COLORS[t])
            for t, n in [
                ("M", "Module"),
                ("C", "Class"),
                ("F", "Function"),
                ("V", "Variable"),
            ]
        )
        click.echo(f"Legend: {legend}")

        for row in df:
            indent = "  " * row["Depth"]
            t = row["Type"]
            type_s = click.style(f"[{t}]", fg=TYPE_COLORS.get(t, "yellow"))
            name = row["Name"].split(".")[-1]

            if t == "F":
                try:
                    # Get the actual function
                    parts = row["Name"].split(".")
                    obj = figrecipe
                    for part in parts[1:]:  # Skip module name
                        obj = getattr(obj, part, None)
                        if obj is None:
                            break
                    if obj and callable(obj):
                        name_s, sig_s = _format_python_signature(obj, indent=indent)
                        click.echo(f"{indent}{type_s} {name_s}{sig_s}")
                    else:
                        name_s = click.style(name, fg="green", bold=True)
                        click.echo(f"{indent}{type_s} {name_s}")
                except Exception:
                    name_s = click.style(name, fg="green", bold=True)
                    click.echo(f"{indent}{type_s} {name_s}")
            else:
                name_s = click.style(name, fg=TYPE_COLORS.get(t, "white"), bold=True)
                click.echo(f"{indent}{type_s} {name_s}")

            if verbose >= 1 and row.get("Docstring"):
                if verbose == 1:
                    doc = row["Docstring"].split("\n")[0][:60]
                    click.echo(f"{indent}    - {doc}")
                else:
                    for ln in row["Docstring"].split("\n"):
                        click.echo(f"{indent}    {ln}")
