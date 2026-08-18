#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figrecipe CLI - Command-line interface for figrecipe."""

from ._main import main

__all__ = ["main"]


# audit §4 — inject version into root --help
try:
    from importlib.metadata import version as _v
    main.help = (
        f"figrecipe (v{_v('figrecipe')}) — "
        + (main.help or "").lstrip()
    )
except Exception:
    pass

# audit-cli §1a — packages with _skills/ MUST expose
# `<cli> skills {list,get,install}`.
#
# §13 puts self-maintenance commands under `dev`, so the group's home is
# `figrecipe dev skills` and the top-level spelling is a deprecation alias
# that forwards to it. The two rules are satisfied by the same pair: §1a
# gets a working `figrecipe skills ...`, §13 gets the canonical location.
#
# Registered HERE rather than in _main.py because this is where the group
# has always been attached, and doing it in both places is what hid the
# problem: _main.py added scitex-dev's generic skills group to `main` and
# this line overwrote it, so the alias _main.py registered was replaced
# before anyone could invoke it. Measured 2026-08-18 — the alias carried
# its `_deprecated_alias` metadata and `main.commands["skills"]` was still
# the plain group, so §13 kept firing against a fix that looked applied.
from ._skills import skills_group as _skills_group

main.commands["dev"].add_command(_skills_group, name="skills")

try:
    from scitex_dev.ecosystem import deprecated_alias

    deprecated_alias(
        main,
        "skills",
        target=_skills_group,
        target_name="dev skills",
        remove_in="1.0",
        phase="warn",
    )
except ImportError:
    main.add_command(_skills_group, name="skills")
