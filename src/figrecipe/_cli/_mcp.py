#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP server commands for figrecipe."""

import click

from ._json_output import json_requested


@click.group(invoke_without_command=True)
@click.option("--help-recursive", is_flag=True, help="Show help for all subcommands")
@click.pass_context
def mcp(ctx, help_recursive):
    """MCP (Model Context Protocol) server commands."""
    if help_recursive:
        _print_help_recursive(ctx)
        ctx.exit(0)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _print_help_recursive(ctx):
    """Print help for mcp and all its subcommands."""
    fake_parent = click.Context(click.Group(), info_name="figrecipe")
    parent_ctx = click.Context(mcp, info_name="mcp", parent=fake_parent)

    click.secho("━━━ figrecipe mcp ━━━", fg="cyan", bold=True)
    click.echo(mcp.get_help(parent_ctx))

    for name in sorted(mcp.list_commands(ctx) or []):
        cmd = mcp.get_command(ctx, name)
        if cmd is None:
            continue
        click.echo()
        click.secho(f"━━━ figrecipe mcp {name} ━━━", fg="cyan", bold=True)
        with click.Context(cmd, info_name=name, parent=parent_ctx) as sub_ctx:
            click.echo(cmd.get_help(sub_ctx))


@mcp.command("start")
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=8000, type=int, help="Port to bind to.")
@click.option("--dry-run", is_flag=True, help="Print launch plan without starting.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def start_server(host: str, port: int, dry_run: bool, yes: bool) -> None:
    """Start the figrecipe MCP server.

    \b
    Example:
      $ figrecipe mcp start
      $ figrecipe mcp start --host 0.0.0.0 --port 9000
      $ figrecipe mcp start --dry-run
    """
    if dry_run:
        click.echo(f"DRY RUN — would start figrecipe MCP server on {host}:{port}")
        return
    try:
        from .._mcp.server import mcp as mcp_server
    except ImportError as e:
        raise click.ClickException(
            f"Failed to import MCP server. Install fastmcp: pip install fastmcp\n{e}"
        ) from e

    click.echo(f"Starting figrecipe MCP server on {host}:{port}")
    mcp_server.run()


def _extract_return_keys(description: str) -> list:
    """Extract return dict keys from docstring Returns section."""
    import re

    if not description or "Returns" not in description:
        return []
    match = re.search(
        r"Returns\s*[-]+\s*\w+\s*(.+?)(?:Raises|Examples|Notes|\Z)",
        description,
        re.DOTALL,
    )
    if not match:
        return []
    return re.findall(r"'([a-z_]+)'", match.group(1))


def _format_signature(tool, multiline: bool = False, indent: str = "  ") -> str:
    """Format tool as Python-like function signature with return type."""
    import inspect

    params = []
    if hasattr(tool, "parameters") and tool.parameters:
        schema = tool.parameters
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for name, info in props.items():
            ptype = info.get("type", "any")
            default = info.get("default")
            if name in required:
                p = f"{click.style(name, fg='white', bold=True)}: {click.style(ptype, fg='cyan')}"
            elif default is not None:
                def_str = repr(default) if len(repr(default)) < 20 else "..."
                p = f"{click.style(name, fg='white', bold=True)}: {click.style(ptype, fg='cyan')} = {click.style(def_str, fg='yellow')}"
            else:
                p = f"{click.style(name, fg='white', bold=True)}: {click.style(ptype, fg='cyan')} = {click.style('None', fg='yellow')}"
            params.append(p)
    # Get return type from function annotation + dict keys from docstring
    ret_type = ""
    if hasattr(tool, "fn") and tool.fn:
        try:
            sig = inspect.signature(tool.fn)
            if sig.return_annotation != inspect.Parameter.empty:
                ret = sig.return_annotation
                ret_name = ret.__name__ if hasattr(ret, "__name__") else str(ret)
                keys = (
                    _extract_return_keys(tool.description) if tool.description else []
                )
                keys_str = (
                    click.style(f"{{{', '.join(keys)}}}", fg="yellow") if keys else ""
                )
                ret_type = f" -> {click.style(ret_name, fg='magenta')}{keys_str}"
        except Exception:
            pass
    name_s = click.style(tool.name, fg="green", bold=True)
    if multiline and len(params) > 2:
        param_indent = indent + "    "
        params_str = ",\n".join(f"{param_indent}{p}" for p in params)
        return f"{indent}{name_s}(\n{params_str}\n{indent}){ret_type}"
    return f"{indent}{name_s}({', '.join(params)}){ret_type}"


def _estimate_tokens(text: str) -> int:
    """Estimate token count (rough: ~4 chars per token)."""
    return len(text) // 4 if text else 0


def _get_tools_dict(mcp_server) -> dict:
    """Get tools as {name: tool_obj} dict, compatible with FastMCP v2+."""
    import asyncio

    tools_list = asyncio.run(mcp_server.list_tools())
    return {t.name: t for t in tools_list}


def _get_mcp_summary(mcp_server) -> dict:
    """Get MCP server summary statistics."""
    import json as json_mod

    tools = list(_get_tools_dict(mcp_server).values())
    instructions = getattr(mcp_server, "instructions", "") or ""
    total_desc = sum(len(t.description or "") for t in tools)
    total_params = sum(
        len(json_mod.dumps(t.parameters))
        if hasattr(t, "parameters") and t.parameters
        else 0
        for t in tools
    )

    return {
        "name": getattr(mcp_server, "name", "unknown"),
        "tool_count": len(tools),
        "instructions_tokens": _estimate_tokens(instructions),
        "descriptions_tokens": _estimate_tokens("x" * total_desc),
        "schemas_tokens": _estimate_tokens("x" * total_params),
        "total_context_tokens": (
            _estimate_tokens(instructions)
            + _estimate_tokens("x" * total_desc)
            + _estimate_tokens("x" * total_params)
        ),
    }


@mcp.command("list-tools")
@click.option("-v", "--verbose", count=True, help="Verbosity: -v, -vv, -vvv.")
@click.option("-c", "--compact", is_flag=True, help="Compact signatures (single line)")
@click.option(
    "--module",
    "-m",
    type=str,
    default=None,
    help="Filter by module (plt, diagram)",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option("--summary", "show_summary", is_flag=True, help="Show context summary.")
def list_tools(
    verbose: int, compact: bool, module: str, as_json: bool, show_summary: bool
) -> None:
    """List available MCP tools.

    Verbosity: (none) names, -v signatures, -vv +description, -vvv full.
    Signatures are expanded by default; use -c/--compact for single line.

    \b
    Example:
      $ figrecipe mcp list-tools
      $ figrecipe mcp list-tools -vv
      $ figrecipe mcp list-tools --json --module plt
    """
    as_json = json_requested(as_json)

    try:
        from .._mcp.server import mcp as mcp_server
    except ImportError as e:
        raise click.ClickException(
            f"fastmcp not installed. Install with: pip install figrecipe[mcp]\n{e}"
        ) from e

    # Get all tools (single async call, cache result)
    _tools_dict = _get_tools_dict(mcp_server)
    tools = list(_tools_dict.keys())

    # Group by module prefix
    modules = {}
    for tool in sorted(tools):
        prefix = tool.split("_")[0]
        if prefix not in modules:
            modules[prefix] = []
        modules[prefix].append(tool)

    # Filter by module if specified
    if module:
        module = module.lower()
        if module not in modules:
            click.secho(f"ERROR: Unknown module '{module}'", fg="red", err=True)
            click.echo(f"Available modules: {', '.join(sorted(modules.keys()))}")
            raise SystemExit(1)
        modules = {module: modules[module]}

    summary = _get_mcp_summary(mcp_server)

    if as_json:
        import json

        output = {
            "summary": summary,
            "total": sum(len(t) for t in modules.values()),
            "modules": {},
        }
        for mod, tool_list in modules.items():
            output["modules"][mod] = {
                "count": len(tool_list),
                "tools": [],
            }
            for tool_name in tool_list:
                tool_obj = _tools_dict.get(tool_name)
                schema = tool_obj.parameters if hasattr(tool_obj, "parameters") else {}
                output["modules"][mod]["tools"].append(
                    {
                        "name": tool_name,
                        "signature": _format_signature(tool_obj)
                        if tool_obj
                        else tool_name,
                        "description": tool_obj.description if tool_obj else "",
                        "parameters": schema,
                    }
                )
        click.echo(json.dumps(output, indent=2))
    else:
        total = sum(len(t) for t in modules.values())
        click.secho(f"FigRecipe MCP: {summary['name']}", fg="cyan", bold=True)
        click.echo(f"Tools: {total} ({len(modules)} modules)")
        if show_summary:
            click.echo(f"Context: ~{summary['total_context_tokens']:,} tokens")
            click.echo(f"  Instructions: ~{summary['instructions_tokens']:,} tokens")
            click.echo(f"  Descriptions: ~{summary['descriptions_tokens']:,} tokens")
            click.echo(f"  Schemas: ~{summary['schemas_tokens']:,} tokens")
        click.echo()

        for mod, tool_list in sorted(modules.items()):
            click.secho(f"{mod}: {len(tool_list)} tools", fg="green", bold=True)
            for tool_name in tool_list:
                tool_obj = _tools_dict.get(tool_name)

                if verbose == 0:
                    # Names only
                    click.echo(f"  {tool_name}")
                elif verbose == 1:
                    # Full signature
                    sig = (
                        _format_signature(tool_obj, multiline=not compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    click.echo(sig)
                elif verbose == 2:
                    # Signature + one-line description
                    sig = (
                        _format_signature(tool_obj, multiline=not compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    click.echo(sig)
                    if tool_obj and tool_obj.description:
                        desc = tool_obj.description.split("\n")[0].strip()
                        click.echo(f"    {desc}")
                    click.echo()
                else:
                    # Signature + full description
                    sig = (
                        _format_signature(tool_obj, multiline=not compact)
                        if tool_obj
                        else f"  {tool_name}"
                    )
                    click.echo(sig)
                    if tool_obj and tool_obj.description:
                        for line in tool_obj.description.strip().split("\n"):
                            click.echo(f"    {line}")
                    click.echo()
            click.echo()


@mcp.command("doctor")
def doctor() -> None:
    """Check MCP server dependencies and configuration.

    \b
    Example:
      $ figrecipe mcp doctor
    """
    click.echo("Checking MCP dependencies...")

    # Check fastmcp
    try:
        import fastmcp

        click.echo(f"  ✓ fastmcp {fastmcp.__version__}")
    except ImportError:
        click.echo("  ✗ fastmcp not installed")
        click.echo("    Install with: pip install figrecipe[mcp]")
        return

    # Check server imports
    try:
        from .._mcp.server import mcp as mcp_server

        click.echo(f"  ✓ MCP server loaded ({len(_get_tools_dict(mcp_server))} tools)")
    except Exception as e:
        click.echo(f"  ✗ MCP server error: {e}")
        return

    click.echo("\nMCP server is ready.")
    click.echo("Run with: figrecipe mcp start")


@mcp.command("install")
@click.option("--claude-code", is_flag=True, help="Show Claude Code config.")
@click.option(
    "--dry-run", is_flag=True, help="Print install plan without performing it."
)
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def install(claude_code: bool, dry_run: bool, yes: bool) -> None:
    """Show MCP server installation instructions.

    \b
    Example:
      $ figrecipe mcp install
      $ figrecipe mcp install --claude-code
      $ figrecipe mcp install --dry-run
    """
    if dry_run:
        click.echo("DRY RUN — printing install instructions only")
    if claude_code:
        click.echo("Add to your Claude Code MCP config:")
        click.echo()
        click.echo('  "figrecipe": {')
        click.echo('    "command": "figrecipe",')
        click.echo('    "args": ["mcp", "start"]')
        click.echo("  }")
    else:
        click.echo("figrecipe MCP Server Installation")
        click.echo("=" * 40)
        click.echo()
        click.echo("1. Install MCP dependencies:")
        click.echo("   pip install figrecipe[mcp]")
        click.echo()
        click.echo("2. For Claude Code, add to MCP config:")
        click.echo("   figrecipe mcp install --claude-code")
        click.echo()
        click.echo("3. Test the server:")
        click.echo("   figrecipe mcp doctor")


@mcp.command("info")
def info() -> None:
    """Show MCP server information.

    \b
    Example:
      $ figrecipe mcp info
    """
    try:
        from .._mcp.server import mcp as mcp_server
    except ImportError as e:
        raise click.ClickException(
            f"fastmcp not installed. Install with: pip install figrecipe[mcp]\n{e}"
        ) from e

    click.echo("figrecipe MCP Server")
    click.echo("=" * 40)
    click.echo()
    click.echo("Available tools:")
    for tool in _get_tools_dict(mcp_server).values():
        click.echo(f"  - {tool.name}")
    click.echo()
    click.echo("Usage:")
    click.echo("  figrecipe mcp start")
    click.echo("  fastmcp run figrecipe._mcp.server:mcp")
