"""Shared JSON preference for leaf CLI commands with a JSON output option."""

import click


def json_requested(local_flag: bool) -> bool:
    """Honor root JSON preferences, including direct calls without a context."""
    context = click.get_current_context(silent=True)
    root_options = context.find_root().obj if context is not None else None
    return local_flag or (
        isinstance(root_options, dict) and bool(root_options.get("as_json"))
    )
