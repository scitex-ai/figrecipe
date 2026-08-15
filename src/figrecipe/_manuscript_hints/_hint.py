#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One figure-quality finding, in the shape scitex-writer's Details pane reads.

WHY THIS IS A VALIDATED DATACLASS AND NOT A DICT. figrecipe is the THIRD
producer writing into a feed that scitex-writer and clew also write. Their
reader validates almost nothing — it checks ``isinstance(data.get("hints"),
list)`` and renders whatever is inside — so a wrong key here does not fail
here. It fails silently in someone else's UI, as a hint that renders blank or
not at all, and the person who sees it has no way back to figrecipe. A
validator makes the shape fail where it is BUILT instead.

THE FIELD CONTRACT IS UNCONFIRMED. scitex-writer's reader does not declare the
per-hint keys, and only ``hint.location`` greps cleanly out of their frontend.
The keys below are figrecipe's assumption, stated on
figrecipe-manuscript-hints-producer-20260714 and sent to scitex-writer
directly on 2026-08-15 with an offer to correct them. Until they confirm,
treat ``HINT_KEYS`` as provisional — it is deliberately in ONE place so that
correcting it is a one-line change rather than a hunt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

#: Producer name figrecipe stamps on every hint it emits. This is the merge
#: key: writing the feed replaces exactly the entries carrying this source and
#: leaves every other producer's entries untouched.
SOURCE = "figrecipe"

#: The per-hint keys figrecipe emits. PROVISIONAL — see the module docstring.
HINT_KEYS: Tuple[str, ...] = (
    "source",
    "claim_id",
    "kind",
    "severity",
    "message",
    "location",
)

#: Severity ladder, ordered least to most urgent. Closed set: an unknown
#: severity would sort and colour arbitrarily in a UI that does not validate.
SEVERITIES: Tuple[str, ...] = ("info", "warning", "error")

#: What kind of figure problem this hint reports. Closed set for the same
#: reason as SEVERITIES, and because ``summary.by_kind`` is keyed on it.
KINDS: Tuple[str, ...] = (
    "stale-recipe",
    "missing-recipe",
    "missing-figure",
    "unrecorded-output",
    "lint",
)


class HintValidationError(ValueError):
    """A hint was built with a shape the feed cannot carry.

    Raised at construction, naming the offending field, the offending value,
    and the valid set — so the message is enough to fix the call without
    opening this module.
    """


@dataclass(frozen=True)
class Hint:
    """A single figure-quality finding bound to one manuscript claim.

    Frozen because a hint is a measurement, not a workspace: once built it
    describes what was true of a file at scan time, and mutating it after the
    fact would make the feed disagree with the disk it was derived from.

    Parameters
    ----------
    kind
        One of :data:`KINDS`.
    severity
        One of :data:`SEVERITIES`.
    message
        Human-readable, and ACTIONABLE — say what to do, not only what broke.
    claim_id
        The manuscript claim this figure backs. figrecipe derives it from the
        figure's project-relative path with the extension stripped.
    location
        Where the problem is, for the reader to display. figrecipe uses the
        project-relative path of the offending file.
    source
        Producer name; defaults to :data:`SOURCE` and should not be overridden
        except in tests, since it is the merge key.
    """

    kind: str
    severity: str
    message: str
    claim_id: str
    location: str
    source: str = field(default=SOURCE)

    def __post_init__(self) -> None:
        self._require_choice("kind", self.kind, KINDS)
        self._require_choice("severity", self.severity, SEVERITIES)
        self._require_text("message", self.message)
        self._require_text("claim_id", self.claim_id)
        self._require_text("location", self.location)
        self._require_text("source", self.source)

    @staticmethod
    def _require_choice(name: str, value: Any, allowed: Tuple[str, ...]) -> None:
        if value not in allowed:
            raise HintValidationError(
                f"Hint.{name}={value!r} is not a recognised value. "
                f"Valid {name}s: {', '.join(allowed)}. "
                f"Add a new one to figrecipe._manuscript_hints._hint if the "
                f"feed should carry it — do not pass an unlisted string, "
                f"because scitex-writer's reader will render it without "
                f"complaint and nobody will notice it is wrong."
            )

    @staticmethod
    def _require_text(name: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise HintValidationError(
                f"Hint.{name}={value!r} must be a non-empty string; got "
                f"{type(value).__name__}. An empty {name} reaches the Details "
                f"pane as a blank row, which reads as a rendering bug rather "
                f"than as a missing value."
            )

    def to_dict(self) -> Dict[str, str]:
        """This hint as the plain dict the feed stores.

        Key order follows :data:`HINT_KEYS` so a hand-read hints.json diffs
        cleanly between runs rather than reshuffling on every write.
        """
        values = {
            "source": self.source,
            "claim_id": self.claim_id,
            "kind": self.kind,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
        }
        return {key: values[key] for key in HINT_KEYS}


# EOF
