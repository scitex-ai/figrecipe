"""`figrecipe skills` — list / get / install agent-facing skills.

Federated (PS-217): the Click group is scitex-dev's shared
``skills_click_group`` primitive bound to the ``figrecipe`` package —
no hand-rolled copy. Registration (under ``figrecipe dev skills`` plus
the top-level deprecation alias) stays in ``figrecipe._cli.__init__``.
"""

from __future__ import annotations

from scitex_dev.cli import skills_click_group

skills_group = skills_click_group(package="figrecipe")

__all__ = ["skills_group"]
