#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coupled invariants: .env walk-up + runtime path separation.

This module documents and re-exports the two coupled behaviors that the
figrecipe top level relies on to honor user configuration without leaking
into install-time state:

1. ``.env`` walk-up — driven by ``scitex_config.load_dotenv(walk_up=True)``
   inside :mod:`figrecipe.__init__`. The call is wrapped so a missing or
   broken scitex-config never breaks ``import figrecipe``.

2. Runtime-path separation — :func:`figrecipe._runtime_paths.runtime_dir`
   resolves to ``<SCITEX_DIR>/figrecipe/runtime/<sub>/`` (never the legacy
   ``<SCITEX_DIR>/figrecipe/<sub>/`` layout) and honors ``SCITEX_DIR``.

The two are coupled because both rely on ``SCITEX_DIR`` (set either via
``.env`` walk-up or directly in the environment) to locate user data.
Tests live in ``tests/figrecipe/test__env_runtime_respect.py`` and the
audit mirror rule (PS-204) requires this module to exist alongside them.
"""

from __future__ import annotations

# Re-export the runtime resolver so the mirror test file has a stable,
# audit-visible aggregator. The top-level ``figrecipe.__init__`` calls
# ``scitex_config.load_dotenv(walk_up=True, stop_at=$HOME)`` directly;
# that import-side behavior cannot be re-exported as a callable, so the
# walk-up half is documented above and verified by the subprocess tests.
from ._runtime_paths import runtime_dir

__all__ = ["runtime_dir"]
