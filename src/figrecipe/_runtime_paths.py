#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-path resolver for figrecipe.

Convention (scitex ecosystem-wide):
    - Static config:   ~/.scitex/figrecipe/<file>            (e.g. config.yaml)
    - Runtime data:    ~/.scitex/figrecipe/runtime/<sub>/    (cache, jobs, ...)

The SCITEX_DIR env var (resolved via scitex-config when available, else falling
back to ``~/.scitex``) is honoured so users can relocate the whole tree.

Public API:
    runtime_dir(sub=None, ensure=True) -> Path
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_PKG = "figrecipe"


def _scitex_dir() -> Path:
    """Return SCITEX_DIR (env var > scitex-config helper > default).

    Defensive: never raises. If scitex-config is unavailable or misbehaves,
    falls back to ``$SCITEX_DIR`` or ``~/.scitex``.
    """
    try:
        from scitex_config import get_scitex_dir  # type: ignore

        return Path(get_scitex_dir()).expanduser()
    except Exception:
        pass

    env_val = os.getenv("SCITEX_DIR")
    if env_val:
        return Path(env_val).expanduser()
    return Path.home() / ".scitex"


def runtime_dir(sub: Optional[str] = None, ensure: bool = True) -> Path:
    """Resolve a figrecipe runtime path.

    Parameters
    ----------
    sub : str, optional
        Sub-resource name (e.g. ``"cache"``, ``"jobs"``). Forward slashes are
        respected so nested resources work: ``runtime_dir("cache/png")``.
        If ``None``, returns the top-level runtime directory.
    ensure : bool, optional
        If True (default), create the directory tree if missing.

    Returns
    -------
    pathlib.Path
        Absolute path under ``<SCITEX_DIR>/figrecipe/runtime[/sub]``.
    """
    base = _scitex_dir() / _PKG / "runtime"
    path = base if not sub else base.joinpath(*str(sub).strip("/").split("/"))
    if ensure:
        path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = ["runtime_dir"]
