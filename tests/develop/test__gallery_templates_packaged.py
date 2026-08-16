#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the built wheel and sdist must CARRY the gallery template assets.

Shipping the assets in the source tree is only half the fix. This repo ignores
``*.png``, ``*.yaml``, ``*.csv`` and ``*.npz`` wholesale, so without explicit
negations git does not track the assets — and what the repo does not carry, a
wheel built from a fresh clone cannot carry either. A build-config change
(an added ``exclude`` entry, a dropped ``artifacts`` stanza combined with
default file selection) can do the same damage while every source-tree test
still passes. The symptom surfaces only in production, as an empty Template
Gallery.

So the build itself is asserted here: build a real wheel and a real sdist and
look inside them. A packaging regression fails the test run instead of the
demo.
"""

import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_SUBPATH = Path("src/figrecipe/_django/gallery_templates")
_ASSET_DIR = _REPO_ROOT / _ASSET_SUBPATH

# Members that must exist inside any built distribution, keyed by extension.
_MIN_YAML = 18
_MIN_PNG = 18


def _source_asset_names(suffix: str) -> list[str]:
    return sorted(p.name for p in _ASSET_DIR.glob(f"*{suffix}"))


# ---------------------------------------------------------------------------
# Source-tree guards — always run, never skipped.
# ---------------------------------------------------------------------------


def test_asset_dir_exists_in_source_tree():
    # Arrange
    asset_dir = _ASSET_DIR

    # Act
    exists = asset_dir.is_dir()

    # Assert
    assert exists, f"gallery template assets missing from the source tree: {asset_dir}"


def test_source_tree_ships_expected_recipe_count():
    # Arrange
    minimum = _MIN_YAML

    # Act
    yamls = _source_asset_names(".yaml")

    # Assert
    assert len(yamls) >= minimum, (
        f"expected at least {minimum} shipped recipes, found {len(yamls)}: {yamls}"
    )


def test_source_tree_ships_expected_thumbnail_count():
    # Arrange
    minimum = _MIN_PNG

    # Act
    pngs = _source_asset_names(".png")

    # Assert
    assert len(pngs) >= minimum, (
        f"expected at least {minimum} shipped thumbnails, found {len(pngs)}: {pngs}"
    )


def test_assets_are_not_git_ignored():
    """A git-ignored asset is an asset a fresh clone does not have.

    The repo's blanket `*.yaml` / `*.png` / `*.csv` / `*.npz` rules would
    swallow these; the negations at the end of .gitignore are what keeps them
    tracked. Untracked assets exist only on the machine that generated them,
    so CI and every release build would ship an empty gallery.
    """
    # Arrange
    sample = sorted(_ASSET_DIR.glob("*.yaml"))[:1]

    # Act — `git check-ignore` exits 0 when the path IS ignored.
    ignored = [
        p
        for p in sample
        if subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "check-ignore", "-q", str(p)],
            capture_output=True,
        ).returncode
        == 0
    ]

    # Assert
    assert ignored == [], (
        f"{ignored} is git-ignored, so it is not tracked and a fresh clone "
        "would build a wheel without it. Add a negation to .gitignore."
    )


# ---------------------------------------------------------------------------
# Built-distribution guards.
# ---------------------------------------------------------------------------


def _build_command(out_dir: Path) -> list[str] | None:
    uv = shutil.which("uv")
    if uv:
        return [uv, "build", "--out-dir", str(out_dir), str(_REPO_ROOT)]
    try:
        import build  # noqa: F401
    except ImportError:
        return None
    return [
        sys.executable,
        "-m",
        "build",
        "--outdir",
        str(out_dir),
        str(_REPO_ROOT),
    ]


@pytest.fixture(scope="module")
def built_dists(tmp_path_factory):
    """Build a real wheel + sdist once for this module."""
    out_dir = tmp_path_factory.mktemp("dist")
    cmd = _build_command(out_dir)
    if cmd is None:
        pytest.skip(
            "no PEP 517 build frontend available (need `uv` on PATH or the "
            "`build` package installed); cannot verify distribution contents"
        )

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        pytest.fail(
            f"build failed ({' '.join(cmd)}):\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )

    wheels = sorted(out_dir.glob("*.whl"))
    sdists = sorted(out_dir.glob("*.tar.gz"))
    assert wheels, f"build produced no wheel in {out_dir}"
    assert sdists, f"build produced no sdist in {out_dir}"
    return {"wheel": wheels[0], "sdist": sdists[0]}


def _wheel_asset_members(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as zf:
        return [
            n
            for n in zf.namelist()
            if "figrecipe/_django/gallery_templates/" in n and not n.endswith("/")
        ]


def _sdist_asset_members(sdist: Path) -> list[str]:
    with tarfile.open(sdist, "r:gz") as tf:
        return [
            m.name
            for m in tf.getmembers()
            if m.isfile() and "_django/gallery_templates/" in m.name
        ]


def test_wheel_contains_gallery_assets(built_dists):
    # Arrange
    wheel = built_dists["wheel"]

    # Act
    members = _wheel_asset_members(wheel)

    # Assert
    assert members, (
        f"the built wheel {wheel.name} contains NO gallery template assets. "
        "The Template Gallery would be empty in every install from this wheel."
    )


def test_wheel_contains_every_source_recipe(built_dists):
    # Arrange
    expected = set(_source_asset_names(".yaml"))

    # Act
    shipped = {
        Path(n).name for n in _wheel_asset_members(built_dists["wheel"])
        if n.endswith(".yaml")
    }

    # Assert
    assert expected <= shipped, f"recipes missing from the wheel: {sorted(expected - shipped)}"


def test_wheel_contains_every_source_thumbnail(built_dists):
    # Arrange
    expected = set(_source_asset_names(".png"))

    # Act
    shipped = {
        Path(n).name for n in _wheel_asset_members(built_dists["wheel"])
        if n.endswith(".png")
    }

    # Assert
    assert expected <= shipped, (
        f"thumbnails missing from the wheel: {sorted(expected - shipped)}"
    )


def test_wheel_contains_template_data_files(built_dists):
    """The CSV/NPZ payloads recipes reference relatively must ship too."""
    # Arrange
    members = _wheel_asset_members(built_dists["wheel"])

    # Act
    data_members = [n for n in members if n.endswith((".csv", ".npz"))]

    # Assert
    assert data_members, (
        "the wheel ships recipes but none of their data files; "
        "'Add to canvas' would fail with FileNotFoundError on every "
        "data-backed template."
    )


def test_sdist_contains_gallery_assets(built_dists):
    # Arrange
    sdist = built_dists["sdist"]

    # Act
    members = _sdist_asset_members(sdist)

    # Assert
    assert members, (
        f"the built sdist {sdist.name} contains NO gallery template assets; "
        "a build-from-source install would have an empty gallery."
    )


# EOF
