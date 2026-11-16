"""Font checks report exact availability, without accepting a fallback face."""

import json

import pytest
from click.testing import CliRunner

from figrecipe._cli import main
from figrecipe._cli._fonts import fonts
from figrecipe.styles._fonts import list_available_fonts


def test_import__cli__fonts_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._cli._fonts"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# The CLI answers whether the requested face exists, rather than whether a
# plotting fallback can be found.

_ABSENT = "SciTeX-Missing-Font-77d19f6b"
_PRESENT = "DejaVu Sans"  # Bundled with Matplotlib.


def test_missing_font_control_is_not_installed():
    # Arrange
    name = _ABSENT
    # Act
    available = list_available_fonts()
    # Assert
    assert name not in available


@pytest.mark.parametrize("name,expected", [(_ABSENT, 1), (_PRESENT, 0)])
def test_font_check_exit_status_matches_exact_availability(name, expected):
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(fonts, ["--check", name, "--json"])
    # Assert
    assert result.exit_code == expected


@pytest.mark.parametrize("name,expected", [(_ABSENT, False), (_PRESENT, True)])
def test_font_check_json_reports_exact_availability(name, expected):
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(fonts, ["--check", name, "--json"])
    # Assert
    assert json.loads(result.stdout) == {"font": name, "available": expected}


@pytest.mark.parametrize(
    "name,expected",
    [
        (_ABSENT, "NOT available"),
        (_PRESENT, "available"),
    ],
)
def test_font_check_text_reports_exact_availability(name, expected):
    # Arrange
    runner = CliRunner()
    # Act
    result = runner.invoke(fonts, ["--check", name])
    # Assert
    assert result.stdout.strip() == f"Font '{name}' is {expected}."


@pytest.mark.parametrize("name,available", [(_ABSENT, False), (_PRESENT, True)])
@pytest.mark.parametrize(
    "flags,structured",
    [
        (["--json", "list-fonts"], True),
        (["list-fonts", "--json"], True),
        (["--json", "list-fonts", "--json"], True),
        (["list-fonts"], False),
    ],
)
def test_root_font_check_honors_json_position(name, available, flags, structured):
    # Arrange
    args = [*flags, "--check", name]
    # Act
    result = CliRunner().invoke(main, args)
    payload = json.loads(result.stdout) if structured else result.stdout.strip()
    expected = (
        {"font": name, "available": available}
        if structured
        else f"Font '{name}' is {'available' if available else 'NOT available'}."
    )
    # Assert
    assert (result.exit_code, payload) == (0 if available else 1, expected)


def test_root_json_supports_filtered_font_inventory():
    # Arrange
    args = ["--json", "list-fonts", "--search", "DejaVu"]
    # Act
    result = CliRunner().invoke(main, args)
    payload = json.loads(result.stdout)
    # Assert
    assert (
        result.exit_code,
        payload["search"],
        "DejaVu Sans" in payload["fonts"],
        all("dejavu" in name.lower() for name in payload["fonts"]),
    ) == (0, "DejaVu", True, True)


def test_root_json_supports_full_font_inventory():
    # Arrange
    args = ["--json", "list-fonts"]
    # Act
    result = CliRunner().invoke(main, args)
    payload = json.loads(result.stdout)
    # Assert
    assert (
        result.exit_code,
        isinstance(payload["fonts"], list),
        "DejaVu Sans" in payload["fonts"],
    ) == (0, True, True)


def test_font_callback_preserves_context_free_json(capsys):
    # Arrange
    name = _PRESENT
    # Act
    fonts.callback(check=name, search=None, as_json=True)
    payload = json.loads(capsys.readouterr().out)
    # Assert
    assert payload == {"font": name, "available": True}
