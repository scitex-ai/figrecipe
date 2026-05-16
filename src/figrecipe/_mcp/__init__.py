#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe MCP server module.

Requires fastmcp>=2.0.0 (Python 3.10+). Install with:
    pip install figrecipe[mcp]
"""

from scitex_dev import try_import_optional

mcp = try_import_optional(
    ".server", "mcp", extra="mcp", pkg="figrecipe", package=__name__
)
__all__ = ["mcp"]
