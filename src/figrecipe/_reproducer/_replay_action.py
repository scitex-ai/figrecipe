#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""The declared shape an argument fixup returns.

A fixup inspects one recorded call before it is replayed and answers two
things: the arguments to call with, and whether to call at all. The second
signal has NO representation in ``(args, kwargs)``, so returning a bare tuple
would let a caller discard it just by unpacking — which is how a recipe that
cannot be honoured gets replayed anyway. Hence one named field per signal.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ReplayAction(Enum):
    """What the caller must do with a fixed-up call."""

    #: Invoke the method with the returned ``args`` / ``kwargs``.
    APPLY = "apply"
    #: Do NOT invoke the method; the recipe could not be honoured faithfully.
    SKIP = "skip"


@dataclass(frozen=True)
class ReplayArgs:
    """The outcome of inspecting one recorded call."""

    action: ReplayAction
    args: Tuple
    kwargs: Dict[str, Any] = field(default_factory=dict)
    #: Why the call was altered or dropped; ``None`` when it passed untouched.
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.action, ReplayAction):
            raise TypeError(
                f"action must be a ReplayAction, got {type(self.action).__name__}"
                f" ({self.action!r}); use ReplayAction.APPLY / .SKIP"
            )
        if self.action is ReplayAction.SKIP and not self.reason:
            raise ValueError(
                "a SKIP result must carry a reason — a dropped call with no "
                "stated cause is indistinguishable from a bug in the fixup"
            )

    @classmethod
    def apply(
        cls,
        args: Tuple,
        kwargs: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> "ReplayArgs":
        """Replay the call, optionally with adjusted arguments."""
        return cls(action=ReplayAction.APPLY, args=args, kwargs=kwargs, reason=reason)

    @classmethod
    def skip(
        cls, args: Tuple, kwargs: Dict[str, Any], reason: str
    ) -> "ReplayArgs":
        """Drop the call. ``reason`` is required and is what the user is told."""
        return cls(action=ReplayAction.SKIP, args=args, kwargs=kwargs, reason=reason)

    @property
    def skipped(self) -> bool:
        """True when the call must not be made."""
        return self.action is ReplayAction.SKIP


__all__ = [
    "ReplayAction",
    "ReplayArgs",
]
