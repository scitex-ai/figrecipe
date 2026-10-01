#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read and write the shared manuscript-hints feed without destroying it.

THE HAZARD THIS MODULE EXISTS FOR. ``.scitex/writer/hints.json`` is written by
THREE producers — scitex-writer, clew, and now figrecipe — and read by
scitex-writer's Details pane. That reader returns the EMPTY feed when the file
is absent, unreadable, OR malformed, and its only shape check is
``isinstance(data.get("hints"), list)``. So a single bad write from any
producer makes all three producers' hints vanish from the UI, displayed
identically to "this paper has not been compiled yet". Nothing says why.

Two consequences drive the whole design here:

1. WRITES ARE ATOMIC. Serialise, validate the serialised bytes, write to a
   temp file in the same directory, then ``os.replace`` — which is atomic on
   POSIX. A crash mid-write leaves the previous feed intact rather than a
   truncated one. Writing in place would make every interrupted run a
   feed-wide outage.

2. AN UNPARSEABLE FEED IS REFUSED, NOT OVERWRITTEN. If the existing file does
   not parse, figrecipe CANNOT know what the other producers had in it, so
   overwriting would silently discard their data to make room for ours. We
   stop and say so instead. This is the one case where refusing to write is
   the safe action and writing is the destructive one.

THREE-VALUED READS. :func:`read_feed` distinguishes ``ok`` / ``absent`` /
``malformed`` rather than collapsing the last two into "empty". That collapse
is precisely the defect that makes the downstream pane ambiguous, and
reproducing it here would leave figrecipe unable to tell "nothing to merge
with" from "something is wrong, do not touch this".
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ._hint import SOURCE, Hint

#: Where the feed lives, relative to the project root.
FEED_RELPATH = Path(".scitex") / "writer" / "hints.json"

#: Schema identifier scitex-writer stamps on the feed. figrecipe preserves
#: whatever it finds and only supplies this when creating the file from
#: scratch — the schema is scitex-writer's to version, not ours.
SCHEMA_ID = "manuscript-hints/1"

#: Read outcomes. ``ok`` = parsed and shaped as expected; ``absent`` = no file
#: (normal before the first compile); ``malformed`` = present but unusable,
#: which is the do-not-touch case.
READ_OK = "ok"
READ_ABSENT = "absent"
READ_MALFORMED = "malformed"


class FeedWriteRefused(RuntimeError):
    """Writing would have destroyed data figrecipe cannot read.

    Carries the offending path and the parse failure, because the fix is
    always "look at that file" and a message without the path sends the
    reader hunting.
    """


@dataclass(frozen=True)
class FeedRead:
    """The result of reading the feed — always this shape, never a bare list.

    ``status`` is one of :data:`READ_OK`, :data:`READ_ABSENT`,
    :data:`READ_MALFORMED`. ``hints`` is meaningful only when status is ok;
    it is empty otherwise, and callers must branch on ``status`` rather than
    on ``not hints``, since those mean different things.
    """

    status: str
    hints: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    schema: Optional[str] = None
    reason: Optional[str] = None

    @property
    def usable(self) -> bool:
        """True when the feed can be merged into. Absent counts as usable."""
        return self.status in (READ_OK, READ_ABSENT)


def feed_path(root: os.PathLike | str) -> Path:
    """The feed's absolute path for a project rooted at ``root``."""
    return Path(root) / FEED_RELPATH


def read_feed(root: os.PathLike | str) -> FeedRead:
    """Read the feed, distinguishing absent from malformed.

    Never raises for a bad file: a malformed feed is a state to report, not an
    exception to propagate, because the caller's correct response is to refuse
    the write rather than to crash a figure save.
    """
    path = feed_path(root)
    if not path.exists():
        return FeedRead(status=READ_ABSENT)

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return FeedRead(status=READ_MALFORMED, reason=f"unreadable: {exc}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return FeedRead(status=READ_MALFORMED, reason=f"invalid JSON: {exc}")

    if not isinstance(data, dict):
        return FeedRead(
            status=READ_MALFORMED,
            reason=f"top level is {type(data).__name__}, expected an object",
        )

    hints = data.get("hints")
    if not isinstance(hints, list):
        return FeedRead(
            status=READ_MALFORMED,
            reason=(
                f"'hints' is {type(hints).__name__}, expected a list"
                if hints is not None
                else "'hints' key is missing"
            ),
        )

    summary = data.get("summary")
    return FeedRead(
        status=READ_OK,
        hints=hints,
        summary=summary if isinstance(summary, dict) else {},
        schema=data.get("schema") if isinstance(data.get("schema"), str) else None,
    )


def merge_by_source(
    existing: Sequence[Dict[str, Any]],
    incoming: Sequence[Hint],
    source: str = SOURCE,
) -> List[Dict[str, Any]]:
    """Replace ``source``'s entries with ``incoming``, keeping everyone else's.

    Replace rather than append: a scan reports the CURRENT state of the
    figures, so last run's stale-recipe hint must disappear once the recipe is
    regenerated. Appending would accumulate contradictory hints forever and
    the pane would show a fixed problem next to its fix.

    Entries whose ``source`` is missing or not a string are treated as
    FOREIGN and preserved. figrecipe only ever removes rows it can positively
    identify as its own — an unlabelled row belongs to somebody, and guessing
    it is ours is how another producer's data gets deleted.
    """
    kept = [
        entry
        for entry in existing
        if not (isinstance(entry, dict) and entry.get("source") == source)
    ]
    return kept + [hint.to_dict() for hint in incoming]


def recompute_summary(hints: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive ``summary`` from ``hints`` so the two cannot disagree.

    The feed stores a denormalised summary that duplicates what is derivable
    from the hints themselves, and nobody owns recomputing it after a
    merge-by-source. If figrecipe merged without recomputing, the pane's
    counts and its list would drift apart silently — and in the direction that
    UNDER-reports, which is the worse direction for a quality feed. So we
    recompute the whole thing from the merged list on every write, including
    the parts other producers contributed.
    """
    by_severity: Dict[str, int] = {}
    by_kind: Dict[str, int] = {}
    for entry in hints:
        if not isinstance(entry, dict):
            continue
        severity = entry.get("severity")
        if isinstance(severity, str):
            by_severity[severity] = by_severity.get(severity, 0) + 1
        kind = entry.get("kind")
        if isinstance(kind, str):
            by_kind[kind] = by_kind.get(kind, 0) + 1
    return {"total": len(hints), "by_severity": by_severity, "by_kind": by_kind}


def write_feed(
    root: os.PathLike | str,
    hints: Sequence[Hint],
    source: str = SOURCE,
) -> Path:
    """Merge ``hints`` into the feed and write it atomically.

    Returns the path written. Raises :class:`FeedWriteRefused` when the
    existing feed cannot be parsed — see the module docstring for why that is
    a refusal rather than an overwrite.
    """
    path = feed_path(root)
    current = read_feed(root)

    if current.status == READ_MALFORMED:
        raise FeedWriteRefused(
            f"Refusing to write {path}: the existing feed is unusable "
            f"({current.reason}). Overwriting it would silently discard the "
            f"hints scitex-writer and clew put there, which figrecipe cannot "
            f"read back. Inspect or delete that file, then re-run — "
            f"figrecipe will recreate it."
        )

    merged = merge_by_source(current.hints, hints, source=source)
    document = {
        "schema": current.schema or SCHEMA_ID,
        "summary": recompute_summary(merged),
        "hints": merged,
    }

    # Serialise BEFORE touching the filesystem: if the payload cannot be
    # encoded, the existing feed must remain exactly as it was.
    payload = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".hints-", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        # Leave no debris behind on any failure path, including interrupts.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


# EOF
