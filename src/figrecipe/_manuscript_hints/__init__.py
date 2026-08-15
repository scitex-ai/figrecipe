#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe._manuscript_hints — emit figure-quality hints for scitex-writer.

figrecipe is the only party that knows whether a figure in a manuscript can
still be regenerated from its recipe. scitex-writer's Details pane shows
per-claim hints from several producers; this package is figrecipe's producer.

Typical use, from a compile step or a maintenance script::

    from figrecipe._manuscript_hints import scan_project, write_feed

    hints = scan_project(project_root)
    write_feed(project_root, hints)

``write_feed`` merges by source — it replaces figrecipe's own entries and
leaves scitex-writer's and clew's alone — recomputes the denormalised summary
so the pane's counts cannot drift from its list, and writes atomically. It
raises :class:`FeedWriteRefused` rather than overwriting a feed it cannot
parse, because that file holds other producers' data.

CONTRACT STATUS: the per-hint field names are figrecipe's assumption, not a
confirmed schema — see :mod:`figrecipe._manuscript_hints._hint`.
"""

from ._feed import (
    FEED_RELPATH,
    READ_ABSENT,
    READ_MALFORMED,
    READ_OK,
    SCHEMA_ID,
    FeedRead,
    FeedWriteRefused,
    feed_path,
    merge_by_source,
    read_feed,
    recompute_summary,
    write_feed,
)
from ._hint import (
    HINT_KEYS,
    KINDS,
    SEVERITIES,
    SOURCE,
    Hint,
    HintValidationError,
)
from ._scan import (
    FIGURE_SUFFIXES,
    RECIPE_SUFFIX,
    STALE_TOLERANCE_S,
    claim_id_for,
    scan_project,
)

__all__ = [
    "FEED_RELPATH",
    "FIGURE_SUFFIXES",
    "HINT_KEYS",
    "KINDS",
    "READ_ABSENT",
    "READ_MALFORMED",
    "READ_OK",
    "RECIPE_SUFFIX",
    "SCHEMA_ID",
    "SEVERITIES",
    "SOURCE",
    "STALE_TOLERANCE_S",
    "FeedRead",
    "FeedWriteRefused",
    "Hint",
    "HintValidationError",
    "claim_id_for",
    "feed_path",
    "merge_by_source",
    "read_feed",
    "recompute_summary",
    "scan_project",
    "write_feed",
]

# EOF
