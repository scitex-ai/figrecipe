"""Regression test for the subprocess-coverage `.pth` shim (tests/conftest.py).

The shim's ``coverage`` import must be nested inside the
``COVERAGE_PROCESS_START`` conditional. It previously sat at module level
before the conditional, so a venv without ``coverage`` installed raised
``ModuleNotFoundError`` on every single interpreter start (not just test
runs) -- surfaced by a user running plain CLI commands like
``figrecipe --help`` in a fresh dev venv.
"""

from __future__ import annotations

import builtins

from tests.conftest import _ensure_subprocess_coverage_shim


def test_shim_pth_content_guards_coverage_import_behind_env_check(
    tmp_path, monkeypatch
):
    # Arrange
    monkeypatch.setattr(
        "tests.conftest.sysconfig.get_paths", lambda: {"purelib": str(tmp_path)}
    )
    monkeypatch.delenv("COVERAGE_PROCESS_START", raising=False)

    # Act
    _ensure_subprocess_coverage_shim()
    pth_text = (tmp_path / "_figrecipe_subprocess_coverage.pth").read_text()

    # Assert
    assert pth_text.index("import coverage") > pth_text.index("if os.environ.get(")


def test_shim_does_not_import_coverage_when_env_var_unset(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr(
        "tests.conftest.sysconfig.get_paths", lambda: {"purelib": str(tmp_path)}
    )
    monkeypatch.delenv("COVERAGE_PROCESS_START", raising=False)
    _ensure_subprocess_coverage_shim()
    pth_text = (tmp_path / "_figrecipe_subprocess_coverage.pth").read_text()

    real_import = builtins.__import__

    def _blocking_import(name, *args, **kwargs):
        if name == "coverage":
            raise ModuleNotFoundError("simulated: coverage not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocking_import)

    # Act / Assert (must not raise, since COVERAGE_PROCESS_START is unset)
    exec(compile(pth_text, "_figrecipe_subprocess_coverage.pth", "exec"), {})
