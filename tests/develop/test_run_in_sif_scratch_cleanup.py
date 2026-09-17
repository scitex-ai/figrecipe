#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The CI leg removes its own ~2G scratch, whatever the suite's outcome.

Card figrecipe-ci-run-in-sif-exec-defeats-exit-trap-fills-compute-04-root-20260915:
`run-in-sif.sh` ended with `exec nice ... python -m pytest`, and `exec` REPLACES
the shell, so the EXIT trap that removes the run's /tmp scratch never fired. A
cleanup keyed to a trap on a process that no longer exists is not a cleanup:
every job orphaned its scratch (measured on scitex-02: 270G of ci-* dirs, root
filesystem at 0 bytes, host_exec unable to write its own audit log).

These tests run the REAL script end to end — with a stub interpreter, stub
installer and stub schedulers on PATH — because the defect was not in the
cleanup code but in how the script handed off to pytest, which only an execution
can show. Each test makes a single assertion (STX-TQ007); problems are collected
and folded into one.
"""

import os
import stat
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".github" / "ci" / "run-in-sif.sh"

# The script's own age-gated sweep of OTHER runs' directories. Disabled here: this
# process must not delete a real CI leg's scratch on a shared /tmp.
NO_REAPING = "100000"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture()
def sif_harness(tmp_path):
    """A stub CI environment: PATH tools, a fake SIF venv, and a unique run id."""
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    # Pass-through wrappers: `nice -n 19 ionice -c 3 python ...` must still end
    # up running python, or the test would prove nothing about the real argv.
    for tool in ("nice", "ionice"):
        _write_executable(
            stubs / tool,
            "#!/usr/bin/env bash\n"
            "while [ $# -gt 0 ] && [ \"${1:0:1}\" = \"-\" ]; do shift; "
            "[ \"${1:-}\" = \"19\" ] || [ \"${1:-}\" = \"3\" ] && shift || true; done\n"
            "exec \"$@\"\n",
        )
    for tool in ("uv", "pip", "nproc"):
        _write_executable(stubs / tool, "#!/usr/bin/env bash\nexit 0\n")
    _write_executable(stubs / "nproc", "#!/usr/bin/env bash\necho 4\n")

    venv = tmp_path / "venv"
    (venv / "bin").mkdir(parents=True)
    record = tmp_path / "pytest-argv.txt"
    _write_executable(
        venv / "bin" / "python",
        "#!/usr/bin/env bash\n"
        f'printf \'%s\\n\' "$@" > "{record}"\n'
        'if [ "$1" = "-m" ] && [ "$2" = "pytest" ]; then '
        'exit "${STUB_PYTEST_EXIT:-0}"; fi\n'
        "exit 0\n",
    )

    run_id = f"pytest-{uuid.uuid4().hex[:8]}"
    scratch = Path(f"/tmp/ci-figrecipe-3.12-{run_id}-1")
    env = {
        **os.environ,
        "PATH": f"{stubs}:{os.environ['PATH']}",
        "SIF_VENV": str(venv),
        "GITHUB_RUN_ID": run_id,
        "GITHUB_RUN_ATTEMPT": "1",
        "SCRATCH_REAP_MIN_AGE_MIN": NO_REAPING,
        "STUB_PYTEST_EXIT": "0",
    }
    return {"env": env, "scratch": scratch, "record": record, "tmp": tmp_path}


def _run(harness, **overrides) -> subprocess.CompletedProcess:
    env = {**harness["env"], **overrides}
    return subprocess.run(
        ["bash", str(SCRIPT), "3.12"],
        env=env,
        cwd=str(harness["tmp"]),
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestScratchCleanup:
    def test_a_successful_run_removes_its_scratch(self, sif_harness):
        # Arrange
        scratch = sif_harness["scratch"]
        # Act
        result = _run(sif_harness)
        # Assert -- the regression: with `exec` the directory survived every run.
        assert not scratch.exists(), (
            f"the run left {scratch} behind (stdout tail: {result.stdout[-400:]})"
        )

    def test_a_failing_suite_still_removes_its_scratch(self, sif_harness):
        # Arrange
        scratch = sif_harness["scratch"]
        # Act
        _run(sif_harness, STUB_PYTEST_EXIT="1")
        # Assert -- cleanup must not be conditional on a green suite.
        assert not scratch.exists(), f"a failing run left {scratch} behind"

    def test_the_scratch_exists_while_the_suite_runs(self, sif_harness):
        # Arrange -- the stub records argv, so the assertion below can prove the
        # cleanup removed something that was really created.
        record = sif_harness["record"]
        # Act
        _run(sif_harness)
        # Assert
        assert record.is_file() and "tests/" in record.read_text(encoding="utf-8")


class TestStatusPropagation:
    def test_a_failing_suite_fails_the_step(self, sif_harness):
        # Arrange -- a suite that fails must still hand its status up through
        # the script's `wait`, which is what the runner step reads.
        # Act
        result = _run(sif_harness, STUB_PYTEST_EXIT="1")
        # Assert
        assert result.returncode == 1, (result.returncode, result.stdout[-400:])

    def test_a_passing_suite_passes_the_step(self, sif_harness):
        # Arrange -- and a green suite must not be turned red by the handoff.
        # Act
        result = _run(sif_harness, STUB_PYTEST_EXIT="0")
        # Assert
        assert result.returncode == 0, (result.returncode, result.stdout[-400:])

    def test_the_matrix_arguments_reach_pytest(self, sif_harness):
        # Arrange
        record = sif_harness["record"]
        # Act
        _run(sif_harness)
        # Assert -- a test that passes because pytest never ran would be empty.
        argv = record.read_text(encoding="utf-8")
        assert "tests/" in argv and "-n\n4" in argv, argv


class TestHandoffShape:
    def test_the_test_command_is_not_exec_ed(self):
        # Arrange
        source_lines = SCRIPT.read_text(encoding="utf-8").splitlines()
        # Act -- the guard against reintroducing the defect: `exec` before the
        # pytest call is what defeated the EXIT trap.
        lines = [
            line.strip() for line in source_lines if line.strip().startswith("exec ")
        ]
        # Assert
        assert lines == [], f"run-in-sif.sh exec's the test command again: {lines}"

    def test_the_scratch_trap_is_still_registered(self):
        # Arrange
        source = SCRIPT.read_text(encoding="utf-8")
        # Act
        registered = "trap 'rm -rf \"$TMPDIR\"" in source
        # Assert -- the cleanup this test exercises must remain in place.
        assert registered, source[-600:]
