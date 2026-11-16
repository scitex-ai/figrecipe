#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loosely-coupled scitex-clew provenance recording for figrecipe I/O.

figrecipe records the recipe + data files it writes/reads with scitex-clew
WHEN clew is installed and a ``@stx.session`` is active, so figures and
compositions become nodes in the Clew provenance DAG: a composed figure's
recipe -> its source panel recipes/data -> ... -> raw data. This is what keeps
the provenance chain connected through composition.

Loosely coupled, leaf-respecting (scitex-clew depends on nothing; producers opt
in): clew is reached via scitex-dev's ``try_import_optional`` -- if clew (or
scitex-dev) is absent, or no session is active, every call is a no-op.
Recording is best-effort *observability*; a failure here is logged at debug and
never breaks figrecipe's real save/load (which stays fail-loud on data errors).
"""

from __future__ import annotations

import contextvars
import inspect
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

from .._utils._optional import missing_extra

try:
    import scitex_logging as slogging
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc

_logger = slogging.getLogger(__name__)

# Active ``derived_from`` declaration for outputs recorded in this context.
_DECLARED: contextvars.ContextVar[Optional[Tuple[str, ...]]] = contextvars.ContextVar(
    "figrecipe_clew_declared", default=None
)
# Collector for the files figrecipe reads (see ``collecting_inputs``).
_COLLECTED: contextvars.ContextVar[Optional[List[str]]] = contextvars.ContextVar(
    "figrecipe_clew_collected", default=None
)


def _active_tracker():
    """Return scitex-clew's active-session tracker, or None (no-op safe)."""
    try:
        from scitex_dev import try_import_optional

        clew = try_import_optional("scitex_clew")
        if clew is None:
            return None
        return clew.get_tracker()
    except Exception as exc:  # optional path: clew/scitex-dev unavailable
        _logger.debug("figrecipe: scitex-clew unavailable (%s)", exc)
        return None


def is_tracking() -> bool:
    """True when a scitex-clew session is active (best-effort, never raises)."""
    return _active_tracker() is not None


def record_output(path: Union[str, Path]) -> None:
    """Record ``path`` as a clew output of the active session (best-effort).

    Inside :func:`declaring`, the output is recorded with that
    ``derived_from`` declaration (clew's level-2 minimal slice). A clew too
    old to accept a declaration records the output undeclared.
    """
    tracker = _active_tracker()
    if tracker is None:
        return
    declared = _DECLARED.get()
    try:
        if declared is not None and _accepts_derived_from(tracker):
            tracker.record_output(str(path), derived_from=list(declared))
        else:
            tracker.record_output(str(path))
    except Exception as exc:  # never break the real save
        _logger.debug("figrecipe: clew record_output(%s) failed: %s", path, exc)


def _accepts_derived_from(tracker) -> bool:
    try:
        params = inspect.signature(tracker.record_output).parameters
    except (TypeError, ValueError):
        return False
    return "derived_from" in params


@contextmanager
def declaring(sources: Optional[List[str]]) -> Iterator[None]:
    """Record every figrecipe output in this block as derived from ``sources``.

    ``None`` leaves outputs undeclared (clew keeps every input of the run).
    """
    token = _DECLARED.set(None if sources is None else tuple(sources))
    try:
        yield
    finally:
        _DECLARED.reset(token)


@contextmanager
def collecting_inputs() -> Iterator[List[str]]:
    """Collect the resolved path of every file figrecipe reads in this block.

    Collection does not depend on an active clew session: it is how
    ``reproduce`` learns exactly which files a figure was rebuilt from.
    """
    seen: List[str] = []
    token = _COLLECTED.set(seen)
    try:
        yield seen
    finally:
        _COLLECTED.reset(token)


def record_input(path: Union[str, Path]) -> None:
    """Record ``path`` as a clew input of the active session (best-effort).

    clew auto-links the session(s) that produced ``path`` as parents, which is
    what connects a composed figure to its source panels.
    """
    collected = _COLLECTED.get()
    if collected is not None:
        real = os.path.realpath(str(path))
        if real not in collected:
            collected.append(real)
    tracker = _active_tracker()
    if tracker is None:
        return
    try:
        tracker.record_input(str(path))
    except Exception as exc:  # never break the real load
        _logger.debug("figrecipe: clew record_input(%s) failed: %s", path, exc)


__all__ = ["collecting_inputs", "declaring", "record_input", "record_output"]

# EOF
