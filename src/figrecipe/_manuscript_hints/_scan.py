#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find figures whose recipe and image disagree, by looking at the disk.

figrecipe's promise is that a saved figure can be regenerated from its recipe.
The failure modes that break that promise are visible without importing
anything or replaying anything:

- STALE RECIPE — image and recipe both exist, but one is materially newer than
  the other. Whichever is older no longer describes the other, so replaying
  the recipe produces a figure that is not the one in the manuscript. This is
  the dangerous one, because the figure LOOKS fine; only regeneration reveals
  it, and by then it is in review.
- MISSING RECIPE — an image with no recipe beside it. Not reproducible at all.
- MISSING FIGURE — a recipe whose image is gone. The manuscript's ``\\includegraphics``
  will fail at compile, or worse, silently pick up a stale copy elsewhere.

WHY MTIME AND WHY A TOLERANCE. Modification time is the only ordering signal
available without opening either file, and it is noisy: a checkout, a copy, or
an rsync can move both timestamps. So a difference smaller than
:data:`STALE_TOLERANCE_S` is not reported — that window is wide enough to
absorb "both files written by the same save call" and narrow enough to catch
"someone edited the figure by hand last Tuesday".

WHAT THIS DELIBERATELY DOES NOT DO: decide that a figure is fine. A hint is
evidence of a problem; the absence of a hint is not evidence of correctness,
because this scan cannot see whether the recipe actually reproduces the image.
That check needs a replay and belongs elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from ._hint import Hint

#: Image extensions figrecipe treats as a saved figure.
FIGURE_SUFFIXES: Tuple[str, ...] = (".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff")

#: Recipe sidecar extension. ``save`` writes ``<basename>.yaml`` beside the image.
RECIPE_SUFFIX = ".yaml"

#: Timestamp differences below this many seconds are treated as "written
#: together" rather than as staleness. See the module docstring.
STALE_TOLERANCE_S = 2.0

#: Directories never worth scanning — build output, caches, and vendored
#: trees produce thousands of irrelevant pairs and would bury real findings.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".worktrees",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "_build",
        "build",
        "dist",
        ".old",
    }
)


def _relative(path: Path, root: Path) -> str:
    """``path`` as a project-relative POSIX string, or absolute if outside."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def claim_id_for(path: Path, root: Path) -> str:
    """The manuscript claim a figure backs: its relative path, extension off.

    Extension stripped so an image and its recipe map to the SAME claim — the
    pane groups by claim, and a stale-recipe hint that landed under a
    different claim than the figure it describes would be unfindable.
    """
    relative = _relative(path, root)
    stem, _, _ = relative.rpartition(".")
    return stem or relative


def _mtime(path: Path) -> Optional[float]:
    """``path``'s modification time, or None if it cannot be read.

    None is a real answer, not a zero: an unreadable timestamp means the
    comparison is UNKNOWN, and reporting unknown as "fresh" would let exactly
    the files we cannot inspect pass silently.
    """
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def iter_figures(root: os.PathLike | str) -> Iterable[Path]:
    """Every figure-like file under ``root``, skipping :data:`SKIP_DIR_NAMES`."""
    root_path = Path(root)
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            candidate = Path(dirpath) / name
            if candidate.suffix.lower() in FIGURE_SUFFIXES:
                yield candidate


def iter_recipes(root: os.PathLike | str) -> Iterable[Path]:
    """Every recipe sidecar under ``root``, skipping :data:`SKIP_DIR_NAMES`."""
    root_path = Path(root)
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            candidate = Path(dirpath) / name
            if candidate.suffix.lower() == RECIPE_SUFFIX:
                yield candidate


def _stale_hint(figure: Path, recipe: Path, root: Path) -> Optional[Hint]:
    """A stale-recipe hint for this pair, or None if they agree (or unknown)."""
    figure_mtime = _mtime(figure)
    recipe_mtime = _mtime(recipe)
    if figure_mtime is None or recipe_mtime is None:
        unreadable = figure if figure_mtime is None else recipe
        return Hint(
            kind="stale-recipe",
            severity="info",
            message=(
                f"Could not compare timestamps for {_relative(figure, root)}: "
                f"{_relative(unreadable, root)} has no readable modification "
                f"time, so figrecipe cannot tell whether the recipe still "
                f"describes the image. Check the file's permissions."
            ),
            claim_id=claim_id_for(figure, root),
            location=_relative(unreadable, root),
        )

    drift = figure_mtime - recipe_mtime
    if abs(drift) <= STALE_TOLERANCE_S:
        return None

    if drift > 0:
        newer, older = "image", "recipe"
        remedy = (
            "the image was changed after the recipe that is supposed to "
            "produce it, so replaying the recipe will NOT reproduce the "
            "figure in the manuscript. Re-save through figrecipe."
        )
    else:
        newer, older = "recipe", "image"
        remedy = (
            "the recipe was changed after the image, so the manuscript is "
            "showing output from an older recipe. Re-run the script to "
            "regenerate the figure."
        )

    return Hint(
        kind="stale-recipe",
        severity="warning",
        message=(
            f"{_relative(figure, root)}: the {newer} is "
            f"{abs(drift):.0f}s newer than the {older} — {remedy}"
        ),
        claim_id=claim_id_for(figure, root),
        location=_relative(figure, root),
    )


def scan_project(root: os.PathLike | str) -> List[Hint]:
    """Every disk-visible recipe/figure disagreement under ``root``.

    Returns hints sorted by location so two scans of an unchanged tree produce
    an identical feed — an unstable order would make every write look like a
    change in review.
    """
    root_path = Path(root)
    hints: List[Hint] = []
    recipes_seen: set = set()

    for figure in iter_figures(root_path):
        recipe = figure.with_suffix(RECIPE_SUFFIX)
        if recipe.exists():
            recipes_seen.add(recipe.resolve())
            stale = _stale_hint(figure, recipe, root_path)
            if stale is not None:
                hints.append(stale)
            continue
        hints.append(
            Hint(
                kind="missing-recipe",
                severity="warning",
                message=(
                    f"{_relative(figure, root_path)} has no {RECIPE_SUFFIX} "
                    f"recipe beside it, so it cannot be regenerated. Save it "
                    f"through figrecipe rather than matplotlib's savefig."
                ),
                claim_id=claim_id_for(figure, root_path),
                location=_relative(figure, root_path),
            )
        )

    for recipe in iter_recipes(root_path):
        if recipe.resolve() in recipes_seen:
            continue
        if _has_sibling_figure(recipe):
            continue
        if not _looks_like_recipe(recipe):
            continue
        hints.append(
            Hint(
                kind="missing-figure",
                severity="warning",
                message=(
                    f"{_relative(recipe, root_path)} describes a figure that "
                    f"is not on disk. The manuscript cannot include it — "
                    f"re-run the script that produces it, or delete the "
                    f"recipe if the figure was retired."
                ),
                claim_id=claim_id_for(recipe, root_path),
                location=_relative(recipe, root_path),
            )
        )

    return sorted(hints, key=lambda hint: (hint.location, hint.kind))


def _has_sibling_figure(recipe: Path) -> bool:
    """True when any known image extension exists beside ``recipe``."""
    return any(recipe.with_suffix(suffix).exists() for suffix in FIGURE_SUFFIXES)


def _looks_like_recipe(path: Path) -> bool:
    """True when this .yaml is plausibly a figrecipe recipe.

    Most .yaml files in a repository are configuration, not recipes, and
    reporting every one of them as a missing figure would make the feed
    useless. figrecipe recipes carry a top-level marker key; we look for it
    textually rather than parsing, because this runs over a whole tree and a
    YAML parse of every config file is both slow and able to raise.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return False
    return "figrecipe" in head


# EOF
