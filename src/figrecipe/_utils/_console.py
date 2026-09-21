#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe's console-output transports.

figrecipe emits its status, progress and CLI output through scitex-logging, so
those lines carry the ecosystem's aligned ``INFO:``/``SUCC:``/``WARN:``/
``ERRO:`` prefixes and the same level-aware, filterable record every other
SciTeX package produces. scitex-logging is a hard dependency of figrecipe, so
there is no fallback path here: a bare ``import figrecipe`` always has it.

Three transports, each matching one of the carve-outs the ecosystem's PS-220
rule recognises STRUCTURALLY (a `print` is spared only when a static reader can
mechanically prove it is data transport, never by a comment):

``get_logger(name)``
    scitex-logging's logger. Diagnostics about work figrecipe is doing.

``get_console(name)``
    scitex-logging's stdout console (``scitex_logging.getConsole``). This is the
    transport for human-facing output that must stay on STDOUT -- CLI command
    results, report tables, demo scripts. It changes nothing about the stream
    the reader sees; it adds the level.

``render_content(content)``
    The explicit content-rendering contract: print caller-supplied, already
    rendered content to stdout VERBATIM. Reserved for the outputs whose exact
    bytes are a published contract (a ``--version`` line, a shell-completion
    script that gets ``source``d), where a level prefix would corrupt the
    payload rather than clarify it. It is deliberately not a general ``print``
    hatch -- the doc's ONE `print` lives here and nowhere else.

``render_rich(renderable, name)``
    Rich's ``Console.print`` writes to a console stream that carries no level
    and no searchable record, and PS-220 forbids it in shippable source. The
    renderable is rendered with Rich's own renderer to text -- the console
    stream is never written to -- and that text is emitted as ONE levelled
    record on the stdout console. This is the same transport scitex-dev's
    ``_core/streams.py`` documents and uses for its own CLI tables.

Caller-owned streams (a ``file=`` parameter the CALLER supplies) are the fourth
carve-out and are not funnelled through here: figrecipe honours the caller's
stream at the call site.
"""

from __future__ import annotations

from typing import Any

__all__ = ["get_console", "get_logger", "render_content", "render_rich"]


def get_logger(name: str = "figrecipe") -> Any:
    """Return scitex-logging's logger for ``name``.

    Parameters
    ----------
    name : str
        Logger name; pass ``__name__`` from the call site.
    """
    import scitex_logging as slogging

    return slogging.getLogger(name)


def get_console(name: str = "figrecipe") -> Any:
    """Return scitex-logging's STDOUT console for ``name``.

    Use this rather than the logger when the output is the command's product
    and has to stay on stdout. Suffix the name with ``".console"`` to keep the
    console channel distinct from the logger channel, matching the convention
    scitex-dev's own CLI uses.

    Parameters
    ----------
    name : str
        Console name; pass ``__name__`` from the call site.
    """
    import scitex_logging as slogging

    return slogging.getConsole(name)


def render_content(content: str) -> None:
    """Print caller-supplied, already-rendered content verbatim to stdout.

    This is the *explicit content-rendering contract* PS-220 recognises
    structurally: the enclosing API is an output operation that emits its
    caller-supplied content unchanged. Reserved for product outputs whose exact
    bytes are published -- a version line, a sourced shell-completion script --
    where a logging level prefix or a hop to stderr would corrupt the payload.

    Parameters
    ----------
    content : str
        The already-rendered text, emitted unchanged.
    """
    print(content)


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
