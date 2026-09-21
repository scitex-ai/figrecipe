#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install hints for figrecipe's optional capabilities.

figrecipe's core install is a matplotlib wrapper. Several features pull a
heavier library that a bare ``pip install figrecipe`` deliberately does not
carry:

============  =================  ==========
import root   distribution       extra
============  =================  ==========
``PIL``       ``Pillow``         ``imaging``
``django``    ``Django``         ``editor``
``networkx``  ``networkx``       ``graph``
``fastmcp``   ``fastmcp``        ``mcp``
``scitex_pd`` ``scitex-pd``      ``scitex``
``scitex_types`` ``scitex-types`` ``scitex``
============  =================  ==========

Every import of one of those libraries is wrapped in a ``try`` that catches
``ImportError`` and calls :func:`missing_extra`, so the failure the user sees
names the extra that supplies the capability instead of a bare
``ModuleNotFoundError``::

    try:
        from django.http import JsonResponse
    except ImportError as exc:  # pragma: no cover - supplied by the
        raise missing_extra(exc) from exc  #       [editor] extra

The guard does NOT silently degrade the capability: the error is re-raised, so
a missing dependency still fails -- at import time for a module-level import,
at call time for a lazy one -- exactly as it did before. Two things change:

* the user gets an install hint naming a real extra rather than a bare
  traceback, and
* the dependency shape is visible to a static reader (the ecosystem audit's
  PS-233 rule reads import statements, not metadata comments), so an
  unguarded hard import of an extra-only distribution can no longer exist.

This mirrors the canonical remedy in scitex-dev's
``03_interface/01_python-api/04_lazy-imports-and-optional-deps.md``.
"""

from __future__ import annotations

# Import root -> (distribution, extra). Kept closed and explicit: a root that
# is not listed here still produces a usable message via the fallback below.
_OPTIONAL: dict[str, tuple[str, str]] = {
    "PIL": ("Pillow", "imaging"),
    "django": ("Django", "editor"),
    "networkx": ("networkx", "graph"),
    "fastmcp": ("fastmcp", "mcp"),
    "scitex_pd": ("scitex-pd", "scitex"),
    "scitex_types": ("scitex-types", "scitex"),
}


def missing_extra(exc: ImportError) -> ImportError:
    """Build the ``ImportError`` to raise for a missing optional dependency.

    Parameters
    ----------
    exc : ImportError
        The error the guarded ``import`` raised. Its ``name`` attribute (set by
        CPython for both ``import x`` and ``from x import y``) selects the
        install hint.

    Returns
    -------
    ImportError
        An error whose message names the distribution and the extra that
        supplies it. Raise it ``from exc`` so the original traceback is kept.
    """
    root = (getattr(exc, "name", None) or "").split(".")[0]
    dist, extra = _OPTIONAL.get(root, (root or "This dependency", "all"))
    return ImportError(
        f"{dist} is required for this capability but is not installed. "
        f"Install it with: pip install 'figrecipe[{extra}]'"
    )


__all__ = ["missing_extra"]

# EOF
