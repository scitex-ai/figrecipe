#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe's console-output transports.

figrecipe emits its status, progress and CLI output through scitex-logging, so
those lines carry the ecosystem's aligned ``INFO:``/``SUCC:``/``WARN:``/
``ERRO:`` prefixes and the same level-aware, filterable record every other
SciTeX package produces. scitex-logging ships in figrecipe's ``[scitex]``
extra, so the imports below are guarded: without the extra they re-raise
with the install hint instead of a bare ``ModuleNotFoundError``.

Output uses the owning scitex-logging primitives throughout. The ecosystem's
PS-220 rule forbids builtin print in source, including exact protocol results:

``get_logger(name)``
    scitex-logging's logger. Diagnostics about work figrecipe is doing.

``get_console(name)``
    scitex-logging's stdout console (``scitex_logging.getConsole``). This is the
    transport for human-facing output that must stay on STDOUT -- CLI command
    results, report tables, demo scripts. It changes nothing about the stream
    the reader sees; it adds the level.

``render_content(content)``
    The explicit content-rendering contract: emit caller-supplied, already
    rendered content to stdout through scitex-logging's plain writer. Reserved
    for the outputs whose exact
    bytes are a published contract (a ``--version`` line, a shell-completion
    script that gets ``source``d), where a level prefix would corrupt the
    payload rather than clarify it. It is deliberately not a general ``print``
    hatch. The writer adds only the existing newline, without logging, level
    filtering, diagnostic capture, or forced flushing.

``render_rich(renderable, name)``
    Rich's ``Console.print`` writes to a console stream that carries no level
    and no searchable record, and PS-220 forbids it in shippable source. The
    renderable is rendered with Rich's own renderer to text -- the console
    stream is never written to -- and that text is emitted as ONE levelled
    record on the stdout console. This is the same transport scitex-dev's
    ``_core/streams.py`` documents and uses for its own CLI tables.

Caller-owned exact streams can use scitex-logging's plain writer with its
``stream=`` argument; builtin print has no stream-based exemption.
"""

from __future__ import annotations

from typing import Any

from ._optional import missing_extra

__all__ = ["get_console", "get_logger", "render_content", "render_rich"]


def get_logger(name: str = "figrecipe") -> Any:
    """Return scitex-logging's logger for ``name``.

    Parameters
    ----------
    name : str
        Logger name; pass ``__name__`` from the call site.
    """
    try:
        import scitex_logging as slogging
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    return slogging.getLogger(name)


def get_console(name: str = "figrecipe") -> Any:
    """Return scitex-logging's STDOUT console for ``name``.

    Use this rather than the logger when the output is the command's product
    and has to stay on stdout. Console and diagnostic names are independent;
    a ``".console"`` suffix can still distinguish their record labels.

    Parameters
    ----------
    name : str
        Console name; pass ``__name__`` from the call site.
    """
    try:
        import scitex_logging as slogging
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    return slogging.getConsole(name)


def render_content(content: str) -> None:
    """Emit caller-supplied, already-rendered content plus a newline to stdout.

    The plain scitex-logging writer retains the exact output contract while
    avoiding builtin print. Reserved for product outputs whose exact
    bytes are published -- a version line, a sourced shell-completion script --
    where a logging level prefix or a hop to stderr would corrupt the payload.

    Parameters
    ----------
    content : str
        The already-rendered text, emitted unchanged.
    """
    try:
        import scitex_logging as slogging
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    slogging.getPlainConsole(__name__).emit(content, flush=False)


def render_rich(renderable: Any, name: str, *, level: str = "info") -> None:
    """Render a Rich renderable through the SciTeX stdout console.

    Rich's ``Console.print`` is forbidden in shippable source (PS-220) and has
    no spare path: it always writes to a console stream that carries no level,
    no aligned prefix and no searchable record. So the renderable (a ``Table``,
    a ``Syntax`` block, a markup string) is rendered with Rich's own renderer to
    text -- the console stream is never written to -- and that text is emitted
    as ONE levelled record on the stdout console. The content a reader sees is
    unchanged; the operator gains the level. Same transport as scitex-dev's
    ``_core/streams.py::render_rich``.

    Parameters
    ----------
    renderable : Any
        Any Rich renderable: ``rich.table.Table``, markup ``str``, ...
    name : str
        Console name -- pass ``__name__`` from the call site.
    level : str
        One of ``info``/``warning``/``error``/``success``.
    """
    from rich.console import Console

    console = Console()
    lines = console.render_lines(renderable, console.options, pad=False)
    text = "\n".join("".join(segment.text for segment in line) for line in lines)
    getattr(get_console(name), level)(text.rstrip("\n"))


# EOF
