#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The warning category replay raises when it cannot re-issue a recorded call.

WHY THIS EXISTS AS A TYPE. Replay failures used to be bare ``warnings.warn``
calls with no category, which made them ``UserWarning`` — indistinguishable
from a font fallback or a layout hint. Two things follow from that, and both
are fixed by naming the type:

- A CALLER CANNOT FILTER THEM. ``filterwarnings("error", category=...)`` is the
  standard way to make a class of problem fatal in a test suite or a pipeline.
  Without a category, "make replay failures fatal" was not expressible.
- WE CANNOT IDENTIFY THEM EITHER. Reproducibility validation reports WHY a
  figure failed to reproduce by quoting what replay complained about, and
  picking those out of the general warning stream needs a reliable predicate.
  Matching on the message text would work until someone rewords a message —
  the constitution's point that pattern matching lies. A category cannot drift.

Deliberately a subclass of ``UserWarning`` rather than a new root: existing
code that filters ``UserWarning`` keeps working unchanged, so introducing this
type silences nothing that was previously visible.
"""

from __future__ import annotations


class ReplayFailureWarning(UserWarning):
    """A recorded call could not be replayed, so the figure will differ.

    Carries no extra state — the message names the method and the underlying
    exception. The value is in the TYPE being checkable.
    """


__all__ = ["ReplayFailureWarning"]

# EOF
