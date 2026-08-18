#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the built wheel and sdist must CARRY the gallery template assets,
every recipe's data must RESOLVE, and every shipped filename must be PORTABLE.

Shipping the assets in the source tree is only half the fix. This repo ignores
``*.png``, ``*.yaml``, ``*.csv`` and ``*.npz`` wholesale, so without explicit
negations git does not track the assets — and what the repo does not carry, a
wheel built from a fresh clone cannot carry either. A build-config change
(an added ``exclude`` entry, a dropped ``artifacts`` stanza combined with
default file selection) can do the same damage while every source-tree test
still passes. The symptom surfaces only in production, as an empty Template
Gallery.

Three distinct failure modes are guarded here, because none of them implies
the others:

1. RESOLUTION — the recipe yaml is present but the ``data:`` file it names is
   not. The gallery then looks healthy and "Add to canvas" dies with
   FileNotFoundError from ``_serializer/_load.py``. Asserting "some data files
   exist" does NOT catch this; the refs themselves must be resolved.
2. PORTABILITY — a generated filename contains a character that is legal on
   ext4 and ILLEGAL on Windows (``*`` is the live example: the recorder
   interpolates the varargs arg name ``*ys`` straight into the filename in
   ``_serializer/_save.py``). ``pip install`` of such a wheel fails at
   EXTRACTION on Windows. No test run on Linux notices.
3. PACKAGING — the files are tracked but the build drops them.

The build itself is asserted, not simulated: a real wheel and a real sdist are
built and opened. A packaging regression fails the test run instead of the demo.
"""

import os
import shutil
import subprocess
import sys
import tarfile
import unicodedata
import zipfile
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_SUBPATH = Path("src/figrecipe/_django/gallery_templates")
_ASSET_DIR = _REPO_ROOT / _ASSET_SUBPATH

# Prefix these assets carry inside a built wheel.
_WHEEL_PREFIX = "figrecipe/_django/gallery_templates/"

# Minimum counts, so a mass deletion cannot pass by shipping a subset.
_MIN_YAML = 18
_MIN_PNG = 18
_MIN_DATA = 57

# Extensions the loader treats as a relative data reference. Kept in sync with
# figrecipe._serializer._load, which accepts exactly these three.
_DATA_SUFFIXES = (".csv", ".npy", ".npz")

# Characters Windows forbids in a filename. `*` and `?` are the ones a
# generated name realistically produces; the rest are here so the guard is a
# statement about portability rather than about one past bug.
_WINDOWS_RESERVED = set('<>:"/\\|?*')

# Reserved DOS device names — still special-cased by Win32 even with a suffix.
_WINDOWS_DEVICE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _source_asset_names(suffix: str) -> list[str]:
    return sorted(p.name for p in _ASSET_DIR.glob(f"*{suffix}"))


def _first_figure_name() -> str:
    """The recipe an empty workspace opens on, read from the handler itself.

    Loaded by file path for the same reason ``tests/.../test_gallery.py``
    does it: ``handlers/__init__`` imports Django models and needs a
    configured app registry, while ``gallery.py`` alone does not. Reading the
    constant instead of repeating the string means renaming the demo cannot
    leave this guard silently checking a name nothing uses.
    """
    import importlib.util

    path = _ASSET_DIR.parent / "handlers" / "gallery.py"
    spec = importlib.util.spec_from_file_location("figrecipe_gallery_pkg", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEMO_TEMPLATE_NAME


def _iter_data_refs(recipe: object):
    """Yield every path-shaped ``data:`` value anywhere in a parsed recipe.

    The recipe schema nests calls under panels under figures and has shifted
    shape before, so this walks the whole tree rather than hard-coding a path.
    Only path-shaped values count: ``data:`` may also carry an inline literal.
    """
    if isinstance(recipe, dict):
        for key, value in recipe.items():
            if (
                key == "data"
                and isinstance(value, str)
                and value.endswith(_DATA_SUFFIXES)
            ):
                yield value
            else:
                yield from _iter_data_refs(value)
    elif isinstance(recipe, list):
        for item in recipe:
            yield from _iter_data_refs(item)


def _portability_complaint(name: str) -> str | None:
    """Return why path COMPONENT ``name`` is non-portable, or None if it is fine."""
    bad = sorted(_WINDOWS_RESERVED & set(name))
    if bad:
        return f"contains Windows-reserved character(s) {bad}"
    ctrl = [c for c in name if ord(c) < 32 or ord(c) == 127]
    if ctrl:
        return f"contains control character(s) {[hex(ord(c)) for c in ctrl]}"
    if name != name.rstrip(" ."):
        return "ends with a space or a dot (silently stripped by Win32)"
    if Path(name).stem.upper() in _WINDOWS_DEVICE_NAMES:
        return "is a reserved DOS device name"
    return None


def _describe_non_ascii(name: str) -> str | None:
    """Return a description of ``name``'s non-ASCII characters, or None."""
    non_ascii = list(dict.fromkeys(c for c in name if ord(c) > 127))
    if not non_ascii:
        return None
    return ", ".join(
        f"{c!r} (U+{ord(c):04X} {unicodedata.name(c, '?')})" for c in non_ascii
    )


def _components(posix_name: str) -> list[str]:
    """Split an archive member name into components (archive names are posix)."""
    return [part for part in posix_name.split("/") if part]


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


def test_source_tree_ships_expected_data_file_count():
    # Arrange
    minimum = _MIN_DATA

    # Act
    data_files = [
        p for p in _ASSET_DIR.rglob("*") if p.is_file() and p.suffix in _DATA_SUFFIXES
    ]

    # Assert
    assert len(data_files) >= minimum, (
        f"expected at least {minimum} recipe data files, found {len(data_files)}. "
        "Recipes without their data cannot be added to the canvas."
    )


def test_source_tree_ships_the_first_figure_recipe():
    """The recipe an empty workspace opens on must exist, by NAME.

    The count guards above pass while shipping 18 OTHER recipes, so losing
    this one would put the first screen a new visitor sees back to a chooser
    with no figure on it — which is the whole defect it was added for.
    """
    # Arrange
    name = _first_figure_name()

    # Act
    recipe = _ASSET_DIR / f"{name}.yaml"

    # Assert
    assert recipe.is_file(), f"the first-figure recipe is missing: {recipe}"


def test_source_tree_ships_the_first_figure_data():
    # Arrange — without its data the seeded figure dies in the loader, and
    # the data-table pane it is supposed to fill stays on "No tables".
    name = _first_figure_name()

    # Act
    data_files = sorted((_ASSET_DIR / f"{name}_data").glob("*.csv"))

    # Assert
    assert data_files, f"the first-figure recipe ships no data: {name}_data/"


@pytest.fixture(scope="module")
def git_ignored_assets() -> list[str]:
    """Assets git refuses to track — one recipe and one data file are enough.

    The data file matters as much as the recipe: the blanket ``**/*.csv`` and
    ``**/*.npz`` rules are the ones that reach into the ``*_data/`` dirs.
    """
    sample = sorted(_ASSET_DIR.glob("*.yaml"))[:1]
    sample += sorted(_ASSET_DIR.glob("*_data/*.csv"))[:1]
    return [
        str(p)
        for p in sample
        if subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "check-ignore", "-q", str(p)],
            capture_output=True,
        ).returncode
        == 0
    ]


def test_assets_are_not_git_ignored(git_ignored_assets):
    """A git-ignored asset is an asset a fresh clone does not have.

    The repo's blanket `*.yaml` / `*.png` / `*.csv` / `*.npz` rules would
    swallow these; the negations at the end of .gitignore are what keeps them
    tracked. Untracked assets exist only on the machine that generated them,
    so CI and every release build would ship an empty gallery.
    """
    # Arrange
    expected = []

    # Act
    actual = git_ignored_assets

    # Assert
    assert actual == expected, (
        f"{git_ignored_assets} is git-ignored, so it is not tracked and a fresh "
        "clone would build a wheel without it. Add a negation to .gitignore."
    )


def _build_source_ref_report() -> dict:
    """Resolve every recipe's ``data:`` refs against the source tree.

    The work lives in a plain function so the module-scoped fixture below has a
    body that only *returns* — a shared fixture that accumulates into its own
    locals reads as cross-test mutable state even when it is not (STX-TQ004).
    """
    pairs = [
        (recipe_path.name, ref)
        for recipe_path in sorted(_ASSET_DIR.glob("*.yaml"))
        for ref in _iter_data_refs(
            yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
        )
    ]
    referenced = {ref for _, ref in pairs}
    broken = [
        f"{recipe_name} -> {ref}"
        for recipe_name, ref in pairs
        if not (_ASSET_DIR / ref).is_file()
    ]
    on_disk = {
        str(p.relative_to(_ASSET_DIR))
        for p in _ASSET_DIR.rglob("*")
        if p.is_file() and p.suffix in _DATA_SUFFIXES
    }
    return {
        "referenced": referenced,
        "broken": broken,
        "orphans": sorted(on_disk - referenced),
    }


@pytest.fixture(scope="module")
def source_ref_report() -> dict:
    """Resolve every recipe's ``data:`` refs against the source tree."""
    return _build_source_ref_report()


def test_source_recipes_actually_declare_data_refs(source_ref_report):
    """If this goes empty the resolution guard below is vacuously green."""
    # Arrange
    report = source_ref_report

    # Act
    referenced = report["referenced"]

    # Assert
    assert referenced, (
        "no path-shaped data refs found in any shipped recipe; either the "
        "recipes lost their data references or _iter_data_refs is wrong. "
        "Either way the resolution guard is no longer checking anything."
    )


def test_every_source_recipe_data_ref_resolves(source_ref_report):
    """GUARD (a): every path-shaped `data:` ref must name a file that exists.

    This is the check that "some data files are present" cannot make. The
    loader joins `data:` onto the recipe's directory LITERALLY
    (`_serializer/_load.py`: `file_path = base_dir / data_ref`) — there is no
    globbing anywhere in the load path — so a ref that does not resolve is a
    guaranteed FileNotFoundError at "Add to canvas" time, not a maybe.
    """
    # Arrange
    total = len(source_ref_report["referenced"])

    # Act
    broken = source_ref_report["broken"]

    # Assert
    assert not broken, (
        f"{len(broken)} of {total} recipe data references do not resolve to a "
        "shipped file. 'Add to canvas' fails with FileNotFoundError on each:\n"
        + "\n".join(f"  {b}" for b in broken)
    )


def test_no_orphaned_source_data_files(source_ref_report):
    """Every shipped data file should be referenced by some recipe.

    Not a correctness bug on its own, but an orphan means the generator and the
    recipes have drifted, which is how a rename gets half-applied.
    """
    # Arrange
    report = source_ref_report

    # Act
    orphans = report["orphans"]

    # Assert
    assert not orphans, f"data files no recipe references: {orphans}"


def _build_source_portability_offenders() -> list[str]:
    return [
        f"{rel}: component {component!r} {complaint}"
        for rel in (
            path.relative_to(_ASSET_DIR)
            for path in sorted(p for p in _ASSET_DIR.rglob("*") if p.is_file())
        )
        for component in rel.parts
        for complaint in [_portability_complaint(component)]
        if complaint
    ]


@pytest.fixture(scope="module")
def source_portability_offenders() -> list[str]:
    return _build_source_portability_offenders()


def test_every_source_asset_filename_is_portable(source_portability_offenders):
    """GUARD (b): no shipped filename may be illegal on Windows.

    `pip install` extracts the wheel using the archive's own member names. A
    member named `stackplot_*ys.csv` cannot be created on NTFS, so the install
    FAILS AT EXTRACTION — the package is simply uninstallable on Windows, and
    no amount of Linux CI notices. The recorder produces such names by
    interpolating the recorded arg name straight into the filename
    (`_serializer/_save.py`), so a regenerated asset set can reintroduce one at
    any time; that is why this is a standing guard and not a one-off cleanup.
    """
    # Arrange
    report = source_portability_offenders

    # Act
    offenders = report

    # Assert
    assert not offenders, (
        f"{len(offenders)} shipped path component(s) are not "
        "portable. A wheel carrying these cannot be pip-installed on Windows "
        "(extraction fails):\n"
        + "\n".join(f"  {o}" for o in source_portability_offenders)
    )


# ---------------------------------------------------------------------------
# Built-distribution guards.
# ---------------------------------------------------------------------------

# Opt-out for the deliberate "no build frontend here" case. Without it, a
# missing `uv`/`build` used to pytest.skip — which made this whole module a
# gate that CANNOT FAIL: the packaging bug it exists to catch would sail
# through any runner that happened to lack a build frontend, reported green.
_SKIP_OPT_OUT = "FIGRECIPE_ALLOW_MISSING_BUILD_FRONTEND"


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
        message = (
            "no PEP 517 build frontend available (need `uv` on PATH or the "
            "`build` package installed); cannot verify distribution contents"
        )
        if os.environ.get(_SKIP_OPT_OUT):
            pytest.skip(f"{message} — skipped via {_SKIP_OPT_OUT}")
        pytest.fail(
            f"{message}.\n"
            "This is a HARD FAILURE on purpose. These are the only tests that "
            "open the actual built artifact; letting them skip turns the "
            "packaging gate into one that cannot fail, which is how an empty "
            "gallery reached production in the first place. Install a build "
            f"frontend, or set {_SKIP_OPT_OUT}=1 to opt out deliberately."
        )

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        pytest.fail(
            f"build failed ({' '.join(cmd)}):\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )

    wheels = sorted(out_dir.glob("*.whl"))
    sdists = sorted(out_dir.glob("*.tar.gz"))
    if not wheels:
        pytest.fail(f"build produced no wheel in {out_dir}")
    if not sdists:
        pytest.fail(f"build produced no sdist in {out_dir}")
    return {"wheel": wheels[0], "sdist": sdists[0]}


def _wheel_asset_members(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as zf:
        return [n for n in zf.namelist() if _WHEEL_PREFIX in n and not n.endswith("/")]


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


def test_wheel_contains_the_first_figure_recipe(built_dists):
    """A build that drops the first figure ships an editor with no figure."""
    # Arrange
    expected = f"{_first_figure_name()}.yaml"

    # Act
    shipped = {Path(n).name for n in _wheel_asset_members(built_dists["wheel"])}

    # Assert
    assert expected in shipped, (
        f"{expected} is not in the built wheel, so an install from it opens "
        "on an empty canvas again."
    )


def test_wheel_contains_the_first_figure_data(built_dists):
    # Arrange
    prefix = f"{_first_figure_name()}_data/"

    # Act
    shipped = [
        n for n in _wheel_asset_members(built_dists["wheel"]) if prefix in n
    ]

    # Assert
    assert shipped, f"the built wheel carries no {prefix} data files"


def test_wheel_contains_every_source_recipe(built_dists):
    # Arrange
    expected = set(_source_asset_names(".yaml"))

    # Act
    shipped = {
        Path(n).name
        for n in _wheel_asset_members(built_dists["wheel"])
        if n.endswith(".yaml")
    }

    # Assert
    assert expected <= shipped, (
        f"recipes missing from the wheel: {sorted(expected - shipped)}"
    )


def test_wheel_contains_every_source_thumbnail(built_dists):
    # Arrange
    expected = set(_source_asset_names(".png"))

    # Act
    shipped = {
        Path(n).name
        for n in _wheel_asset_members(built_dists["wheel"])
        if n.endswith(".png")
    }

    # Assert
    assert expected <= shipped, (
        f"thumbnails missing from the wheel: {sorted(expected - shipped)}"
    )


def _build_wheel_ref_report(wheel: Path) -> dict:
    """Resolve every recipe ref against the WHEEL's own member list.

    The predecessor of this guard asserted only `assert data_members` — that at
    least one .csv/.npz was present. That stays GREEN if 56 of 57 data files are
    dropped from the build, which is precisely the shape of the bug it was meant
    to catch. So the refs are resolved against the archive itself.
    """
    with zipfile.ZipFile(wheel) as zf:
        members = {n for n in zf.namelist() if not n.endswith("/")}
        recipes = sorted(
            n for n in members if n.startswith(_WHEEL_PREFIX) and n.endswith(".yaml")
        )
        pairs = [
            (Path(recipe_name).name, ref)
            for recipe_name in recipes
            for ref in _iter_data_refs(
                yaml.safe_load(zf.read(recipe_name).decode("utf-8"))
            )
        ]
    broken = [
        f"{recipe_name} -> {ref}"
        for recipe_name, ref in pairs
        if _WHEEL_PREFIX + ref not in members
    ]
    return {
        "wheel": wheel.name,
        "recipes": recipes,
        "checked": len(pairs),
        "broken": broken,
    }


@pytest.fixture(scope="module")
def wheel_ref_report(built_dists) -> dict:
    return _build_wheel_ref_report(built_dists["wheel"])


def test_wheel_recipes_declare_data_refs(wheel_ref_report):
    """Without refs to resolve, the wheel resolution guard is vacuously green."""
    # Arrange
    report = wheel_ref_report

    # Act
    checked = report["checked"]

    # Assert
    assert checked, (
        f"no path-shaped data refs found in any recipe inside "
        f"{wheel_ref_report['wheel']}; either the shipped recipes lost their "
        "data references or the parser is wrong."
    )


def test_wheel_data_refs_all_resolve_inside_the_wheel(wheel_ref_report):
    """GUARD (c): the wheel must carry the data its own recipes reference."""
    # Arrange
    report = wheel_ref_report

    # Act
    broken = report["broken"]

    # Assert
    assert not broken, (
        f"the wheel {wheel_ref_report['wheel']} ships recipes whose data files "
        f"it does NOT carry ({len(broken)} of {wheel_ref_report['checked']} refs "
        "unresolved). 'Add to canvas' fails with FileNotFoundError on each:\n"
        + "\n".join(f"  {b}" for b in broken)
    )


def _build_wheel_portability_offenders(wheel: Path) -> list[str]:
    return [
        f"{name}: component {component!r} {complaint}"
        for name in _wheel_asset_members(wheel)
        for component in _components(name)
        for complaint in [_portability_complaint(component)]
        if complaint
    ]


@pytest.fixture(scope="module")
def wheel_portability_offenders(built_dists) -> list[str]:
    return _build_wheel_portability_offenders(built_dists["wheel"])


def test_wheel_member_names_are_portable(wheel_portability_offenders):
    """GUARD (b), at the archive level: the wheel must extract on Windows.

    The source-tree portability test is the fast one; this is the one that
    speaks about the artifact users actually download. A member name illegal on
    NTFS makes `pip install figrecipe` fail during extraction.
    """
    # Arrange
    report = wheel_portability_offenders

    # Act
    offenders = report

    # Assert
    assert not offenders, (
        f"{len(offenders)} wheel member path component(s) are "
        "not portable; `pip install` of this wheel fails at extraction on "
        "Windows:\n" + "\n".join(f"  {o}" for o in wheel_portability_offenders)
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


def test_sdist_contains_template_data_files(built_dists):
    # Arrange
    members = _sdist_asset_members(built_dists["sdist"])

    # Act
    data_members = [n for n in members if n.endswith(_DATA_SUFFIXES)]

    # Assert
    assert len(data_members) >= _MIN_DATA, (
        f"the sdist carries only {len(data_members)} data files, expected at "
        f"least {_MIN_DATA}; a build-from-source install would have a gallery "
        "whose templates cannot be added to the canvas."
    )


# EOF
