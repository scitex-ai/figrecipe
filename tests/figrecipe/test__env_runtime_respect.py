#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the .env-respect + runtime-separation pattern.

Two coupled invariants:

1. Importing figrecipe walks parent dirs for ``.env`` (best-effort) and never
   raises when scitex-config is missing/broken or when no .env exists.
2. ``figrecipe._runtime_paths.runtime_dir(sub)`` resolves to
   ``<SCITEX_DIR>/figrecipe/runtime/<sub>/`` and creates it.

No mocks / monkeypatch — env vars are flipped via yield-based fixtures and
filesystem state via ``tmp_path``.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures (no monkeypatch — pure env-var set/restore)
# ---------------------------------------------------------------------------


@pytest.fixture
def scitex_dir_env(tmp_path):
    """Set SCITEX_DIR to a clean tmp path; restore prior value on teardown."""
    # Arrange: snapshot prior env value.
    prev = os.environ.get("SCITEX_DIR")
    os.environ["SCITEX_DIR"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        if prev is None:
            os.environ.pop("SCITEX_DIR", None)
        else:
            os.environ["SCITEX_DIR"] = prev


@pytest.fixture
def scitex_dir_unset():
    """Ensure SCITEX_DIR is unset for the test; restore on teardown."""
    prev = os.environ.pop("SCITEX_DIR", None)
    try:
        yield
    finally:
        if prev is not None:
            os.environ["SCITEX_DIR"] = prev


# ---------------------------------------------------------------------------
# Change A: .env walk-up call must not break import
# ---------------------------------------------------------------------------


def test_import_figrecipe_exposes_version():
    # Arrange
    sys.modules.pop("figrecipe", None)
    # Act
    mod = importlib.import_module("figrecipe")
    # Assert
    assert isinstance(mod.__version__, str)


def test_import_in_subprocess_with_no_dotenv_succeeds(tmp_path):
    """A subprocess `import figrecipe` from a dir with no .env must exit 0.

    This exercises the real top-level dotenv try/except — no mocks. We run a
    child Python so cwd is a clean tmp_path (no project .env up the chain).
    """
    # Arrange: pristine tmp dir, no .env anywhere up to it.
    work = tmp_path / "no_env"
    work.mkdir()
    # Act
    result = subprocess.run(
        [sys.executable, "-c", "import figrecipe; print(figrecipe.__version__)"],
        cwd=str(work),
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(work)},  # stop walk_up at fake HOME
    )
    # Assert
    assert result.returncode == 0, result.stderr


def _scitex_config_supports_walk_up() -> bool:
    """Return True when the installed scitex_config.load_dotenv accepts walk_up."""
    import inspect

    try:
        from scitex_config import load_dotenv as _ld

        return "walk_up" in inspect.signature(_ld).parameters
    except Exception:
        return False


@pytest.mark.skipif(
    not _scitex_config_supports_walk_up(),
    reason="installed scitex_config.load_dotenv predates walk_up=True kwarg",
)
def test_import_loads_dotenv_from_cwd(tmp_path):
    """A .env in cwd must populate os.environ for a child `import figrecipe`."""
    # Arrange: write a real .env with a sentinel key and a fake HOME so the
    # walk_up terminates at tmp_path.
    work = tmp_path / "with_env"
    work.mkdir()
    (work / ".env").write_text("FIGRECIPE_ENV_RESPECT_PROBE=hello\n")
    script = textwrap.dedent(
        """
        import os
        import figrecipe  # noqa: F401  -- triggers load_dotenv(walk_up=True)
        print(os.environ.get("FIGRECIPE_ENV_RESPECT_PROBE", ""))
        """
    )
    # Act: hand the subprocess PYTHONPATH=<this-package-src> so it picks up the
    # *current* figrecipe (covers both editable installs pointing elsewhere and
    # plain pip installs of an older release).
    import figrecipe as _fr_local

    pkg_src_dir = str(Path(_fr_local.__file__).resolve().parent.parent)
    child_env = {
        k: v for k, v in os.environ.items() if k != "FIGRECIPE_ENV_RESPECT_PROBE"
    }
    child_env["HOME"] = str(work)
    child_env["PYTHONPATH"] = (
        pkg_src_dir + os.pathsep + child_env.get("PYTHONPATH", "")
    ).rstrip(os.pathsep)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(work),
        capture_output=True,
        text=True,
        env=child_env,
    )
    # Assert
    assert result.stdout.strip() == "hello", result.stderr


# ---------------------------------------------------------------------------
# Change B: runtime-path resolver — real filesystem, real env, no mocks
# ---------------------------------------------------------------------------


def test_runtime_dir_uses_runtime_subdir(scitex_dir_env):
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    expected = scitex_dir_env / "figrecipe" / "runtime" / "cache"
    # Act
    out = runtime_dir("cache")
    # Assert
    assert out == expected


def test_runtime_dir_creates_directory(scitex_dir_env):
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    # Act
    out = runtime_dir("cache")
    # Assert
    assert out.is_dir()


def test_runtime_dir_no_sub_returns_runtime_root(scitex_dir_env):
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    expected = scitex_dir_env / "figrecipe" / "runtime"
    # Act
    out = runtime_dir()
    # Assert
    assert out == expected


def test_runtime_dir_nested_sub_path(scitex_dir_env):
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    expected = scitex_dir_env / "figrecipe" / "runtime" / "cache" / "png"
    # Act
    out = runtime_dir("cache/png")
    # Assert
    assert out == expected


def test_runtime_dir_top_level_is_runtime_not_pkg_root(scitex_dir_env):
    """Guard rail: the resolver must NOT return ``<SCITEX>/figrecipe/<sub>``
    (the legacy layout) — runtime must live under a ``runtime/`` sibling.
    """
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    legacy = scitex_dir_env / "figrecipe" / "jobs"
    # Act
    out = runtime_dir("jobs")
    # Assert
    assert out != legacy


def test_runtime_dir_ensure_false_does_not_create(scitex_dir_env):
    # Arrange
    from figrecipe._runtime_paths import runtime_dir

    # Act
    out = runtime_dir("not_yet", ensure=False)
    # Assert
    assert not out.exists()
