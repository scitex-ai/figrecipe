#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``figrecipe.io`` — standardized I/O namespace for the figrecipe package.

Mirrors the ecosystem-wide convention that every scitex / scitex-adjacent
package exposes its I/O verbs under a ``.io`` subpackage (e.g.
``scitex_stats.io``). This lets consumers reach the same primitives
through one predictable path no matter which package they're using:

>>> import figrecipe
>>> from figrecipe.io import save_bundle, load_bundle, reproduce_bundle

>>> import scitex_stats
>>> from scitex_stats.io import save_stats_bundle, load_stats_bundle

The two exceptions to the ``.io`` convention are intentional:

- ``scitex_io`` IS the I/O package — no nested ``scitex_io.io``.
- ``scitex`` (umbrella) re-exposes ``scitex_io`` directly as ``scitex.io``.

Backward compatibility: the top-level ``figrecipe.save_bundle`` /
``figrecipe.load_bundle`` / ``figrecipe.reproduce_bundle`` / ``figrecipe.save``
/ ``figrecipe.load`` / ``figrecipe.reproduce`` continue to work unchanged
(both forms resolve to the same callables).
"""

from .._api._public import load, reproduce, save  # high-level fr.{save,load,reproduce}
from .._bundle import (
    Figz,
    Pltz,
    bundle_exists,
    create_bundle_structure,
    get_bundle_paths,
    is_bundle_path,
    load_bundle,
    reproduce_bundle,
    save_bundle,
)

__all__ = [
    # High-level save / load / reproduce (.png/.pdf/.yaml/.plt.zip/.fig.zip)
    "save",
    "load",
    "reproduce",
    # Bundle primitives
    "save_bundle",
    "load_bundle",
    "reproduce_bundle",
    # Bundle path helpers
    "bundle_exists",
    "create_bundle_structure",
    "get_bundle_paths",
    "is_bundle_path",
    # Bundle classes
    "Figz",
    "Pltz",
]
