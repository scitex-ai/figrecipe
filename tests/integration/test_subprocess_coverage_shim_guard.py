"""Regression test for the subprocess-coverage `.pth` shim (tests/conftest.py).

The shim's ``coverage`` import must be nested inside the
``COVERAGE_PROCESS_START`` conditional. It previously sat at module level
before the conditional, so a venv without ``coverage`` installed raised
``ModuleNotFoundError`` on every single interpreter start (not just test
runs) -- surfaced by a user running plain CLI commands like
``figrecipe --help`` in a fresh dev venv.

No mocks: the "coverage not installed" condition is a REAL environment
(a subprocess launched with `-S`, which skips `site` initialization so no
site-packages -- including wherever `coverage` lives -- end up on
`sys.path`), not a monkeypatched import.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.conftest import _ensure_subprocess_coverage_shim


def test_shim_pth_content_guards_coverage_import_behind_env_check(tmp_path: Path):
    # Arrange: write to a writable tmp dir, not the real site-packages --
    # that may be read-only in CI (e.g. a layered/squashfs SIF image).
    pth_path = _ensure_subprocess_coverage_shim(purelib=tmp_path)
    # Act
    pth_text = pth_path.read_text()
    # Assert
    assert pth_text.index("import coverage") > pth_text.index("if os.environ.get(")


def test_shim_does_not_import_coverage_when_env_var_unset(tmp_path: Path):
    # Arrange
    pth_path = _ensure_subprocess_coverage_shim(purelib=tmp_path)
    pth_text = pth_path.read_text()
    env = dict(os.environ)
    env.pop("COVERAGE_PROCESS_START", None)
    # Act: -S skips site-packages entirely, so `coverage` is genuinely
    # unimportable here -- a real "not installed" condition.
    result = subprocess.run(
        [sys.executable, "-S", "-c", pth_text],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Assert
    assert result.returncode == 0, result.stderr
