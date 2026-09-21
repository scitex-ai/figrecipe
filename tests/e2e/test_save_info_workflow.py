"""End-to-end save → info workflow against real artifacts (PS-212 layer).

Offline (loopback only, no network): a driver script builds a real figure
through the live recording path (matplotlib Agg backend) and `fr.save`
writes `.png + .yaml + data`; the real CLI then reads the recipe back via
`figrecipe info`. Gated by `RUN_E2E=1`, skipped by default. One assert
per test (PA-307).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("RUN_E2E") != "1",
        reason="e2e runs only with RUN_E2E=1",
    ),
]

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = str(_PROJECT_ROOT / "src")

_DRIVER = """\
import matplotlib

matplotlib.use("Agg")

import sys
from pathlib import Path

import numpy as np

import figrecipe as fr

out = Path(sys.argv[1]) / "figure.png"
x = np.linspace(0, 2 * np.pi, 50)
fig, ax = fr.subplots()
ax.plot(x, np.sin(x), id="sine")
fr.save(fig, str(out))
"""


def _run_cli(*args: str, cwd=None) -> subprocess.CompletedProcess[str]:
    """Run the checkout's CLI in a subprocess with an explicit env."""
    env = dict(os.environ, PYTHONPATH=_SRC + os.pathsep + os.environ.get("PYTHONPATH", ""))
    env.setdefault("MPLBACKEND", "Agg")
    return subprocess.run(
        [sys.executable, "-m", "figrecipe", *args],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=cwd,
    )


def _save_recipe(workdir: Path) -> Path:
    """Drive the real save path in a subprocess; return the recipe path."""
    driver = workdir / "make_fig.py"
    driver.write_text(_DRIVER, encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=_SRC + os.pathsep + os.environ.get("PYTHONPATH", ""))
    env.setdefault("MPLBACKEND", "Agg")
    proc = subprocess.run(
        [sys.executable, str(driver), str(workdir)],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=workdir,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"driver save failed:\n{proc.stdout}\n{proc.stderr}")
    return workdir / "figure.yaml"


def test_save_writes_recipe_result_figure_yaml_exists(tmp_path):
    # Arrange — an empty workdir for real figure artifacts.
    workdir = tmp_path / "work"
    workdir.mkdir()
    # Act
    recipe = _save_recipe(workdir)
    # Assert
    assert recipe.is_file()


def test_info_reads_saved_recipe_result_returncode_equals_n_0(tmp_path):
    # Arrange — a real recipe produced through the live save path.
    workdir = tmp_path / "work"
    workdir.mkdir()
    recipe = _save_recipe(workdir)
    # Act
    proc = _run_cli("info", str(recipe), cwd=workdir)
    # Assert
    assert proc.returncode == 0


def test_info_reports_figure_id_result_stdout_contains_figure_id(tmp_path):
    # Arrange — a real recipe produced through the live save path.
    workdir = tmp_path / "work"
    workdir.mkdir()
    recipe = _save_recipe(workdir)
    # Act
    proc = _run_cli("info", str(recipe), cwd=workdir)
    # Assert
    assert "Figure ID" in proc.stdout


# EOF
