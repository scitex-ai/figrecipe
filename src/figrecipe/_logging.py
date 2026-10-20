#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backwards-compatible alias for figrecipe's console transports.

Historically this module hand-rolled a scitex-logging bridge with a plain
``print`` fallback, so figrecipe stayed "dependency-light" when scitex-logging
was absent. Current transports use scitex-logging's diagnostic, stdout, and
plain writers. Missing logging raises the owning ``figrecipe[scitex]`` install
hint rather than falling back to builtin print. Exact result lines retain their
newline and are independent of diagnostic filtering and print capture.

The transports themselves live in :mod:`figrecipe._utils._console`. This module is
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
    """Alias for :func:`figrecipe._utils._console.get_logger`."""
    return get_logger(name)


# EOF
