"""Syntax-only smoke for examples/11_cli_commands.sh (PS303)."""

import subprocess
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "11_cli_commands.sh"


def test_cli_commands_shell_file_exists():
    # Arrange
    # Arrange
    # Act
    # Assert
    target = EXAMPLE
    # Act
    actually_exists = target.exists()
    # Assert
    assert actually_exists, f"missing example: {target}"


def test_cli_commands_passes_bash_syntax_check():
    # Arrange
    # Arrange
    # Act
    # Assert
    target = EXAMPLE
    # Act
    completed = subprocess.run(
        ["bash", "-n", str(target)],
        check=False,
        capture_output=True,
    )
    # Assert
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
