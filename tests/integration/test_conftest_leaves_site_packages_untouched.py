"""Regression test: importing tests/conftest.py must not touch site-packages."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def test_conftest_leaves_site_packages_untouched():
    # Arrange
    conftest = Path(__file__).resolve().parents[1] / "conftest.py"
    assert conftest.is_file()
    child_code = textwrap.dedent(
        f"""\
        import os
        import runpy
        import site

        os.environ["COVERAGE_PROCESS_START"] = "SENTINEL_PROCESS_START"
        os.environ["COVERAGE_FILE"] = "SENTINEL_COVERAGE_FILE"

        def _site_dirs():
            dirs = []
            try:
                dirs.extend(site.getsitepackages())
            except Exception:
                pass
            try:
                dirs.append(site.getusersitepackages())
            except Exception:
                pass
            return dirs

        def _snapshot():
            snap = {{}}
            for d in _site_dirs():
                try:
                    snap[d] = sorted(os.listdir(d))
                except OSError:
                    snap[d] = None
            return snap

        before = _snapshot()
        runpy.run_path({str(conftest)!r}, run_name="conftest_under_test")
        after = _snapshot()
        assert before == after, "conftest modified site-packages contents"
        assert os.environ.get("COVERAGE_PROCESS_START") == "SENTINEL_PROCESS_START"
        assert os.environ.get("COVERAGE_FILE") == "SENTINEL_COVERAGE_FILE"
        """
    )
    # Act
    proc = subprocess.run(
        [sys.executable, "-c", child_code],
        capture_output=True,
        text=True,
    )
    # Assert
    assert proc.returncode == 0, (
        f"child conftest import check failed (exit {proc.returncode}):\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
