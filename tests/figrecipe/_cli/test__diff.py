"""Actual image comparison through the local and root JSON CLI options."""

import json

import pytest
from click.testing import CliRunner
from PIL import Image

from figrecipe._cli import main


@pytest.mark.parametrize("options", [
    ["--json", "diff"],
    ["diff", "--json"],
    ["--json", "diff", "--json"],
])
@pytest.mark.parametrize("changed", [False, True])
def test_diff_json_options_compare_real_pixels(tmp_path, options, changed):
    # Arrange
    original = tmp_path / "original.png"
    reproduced = tmp_path / "reproduced.png"
    image = Image.new("RGB", (10, 10), "white")
    image.save(original)
    image.putpixel((0, 0), (255 * (not changed),) * 3)
    image.save(reproduced)
    # Act
    result = CliRunner().invoke(main, [*options, str(original), str(reproduced)])
    data = json.loads(result.stdout)
    # Assert
    assert (result.exit_code, data["mismatch_pixels"], data["total_pixels"], data["is_match"]) == (
        0, int(changed), 100, not changed,
    )


def test_diff_plain_output_is_readable(tmp_path):
    # Arrange
    path = tmp_path / "same.png"
    Image.new("RGB", (10, 10), "white").save(path)
    # Act
    result = CliRunner().invoke(main, ["diff", str(path), str(path)])
    # Assert
    assert (result.exit_code, "Comparison: MATCH" in result.stdout) == (0, True)
