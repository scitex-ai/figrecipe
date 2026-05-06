#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe CLI - Command-line interface for figrecipe."""

from ._main import main

__all__ = ["main"]


# audit §4 — inject version into root --help
try:
    from importlib.metadata import version as _v
    main.help = (
        f"figrecipe (v{_v('figrecipe')}) — "
        + (main.help or "").lstrip()
    )
except Exception:
    pass
