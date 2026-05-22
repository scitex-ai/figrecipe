"""Compile-only smoke for examples/09b_diagram_NG_patterns.py (PS303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = (
    Path(__file__).resolve().parents[2] / "examples" / "09b_diagram_NG_patterns.py"
)


def test_example_file_exists_on_disk():
    # Arrange
    target = EXAMPLE
    # Act
    actually_exists = target.exists()
    # Assert
    assert actually_exists, f"missing example: {target}"


def test_example_compiles_under_py_compile():
    # Arrange
    target = EXAMPLE
    # Act
    completed = subprocess.run(
        [sys.executable, "-m", "py_compile", str(target)],
        check=False,
        capture_output=True,
    )
    # Assert
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
