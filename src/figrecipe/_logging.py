#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backwards-compatible alias for figrecipe's console transports.

Historically this module hand-rolled a scitex-logging bridge with a plain
``print`` fallback, so figrecipe stayed "dependency-light" when scitex-logging
was absent. scitex-logging is now a hard dependency of figrecipe (the whole
package emits through the ecosystem logging tier), which makes the fallback
dead code -- and a bare ``print`` inside library code cannot be silenced,
redirected or levelled by the caller, which is exactly what the ecosystem's
strict logging tier forbids.

The transports themselves now live in :mod:`figrecipe._console`. This module is
kept as the documented import path for existing internal callers.
"""

from __future__ import annotations

from typing import Any

from ._utils._console import get_console, get_logger, render_content, render_rich

__all__ = [
    "get_console",
    "get_logger",
    "render_content",
    "render_rich",
]


def logger(name: str = "figrecipe") -> Any:
    """Alias for :func:`figrecipe._console.get_logger`."""
    return get_logger(name)


# EOF
