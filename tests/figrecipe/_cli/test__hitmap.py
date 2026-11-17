"""Real image hitmaps preserve JSON statistics and write readable outputs."""

import json

import pytest
from click.testing import CliRunner
from PIL import Image

from figrecipe._cli import main


@pytest.fixture
def images(tmp_path):
    # Arrange
    original = tmp_path / "original.png"
    reproduced = tmp_path / "reproduced.png"
    image = Image.new("RGB", (10, 10), "white")
    image.save(original)
    image.putpixel((0, 0), (0, 0, 0))
    # Act
    image.save(reproduced)
    # Assert: fixture data is deliberately one changed pixel.
    return original, reproduced


@pytest.mark.parametrize("mode", ["diff", "binary", "heatmap"])
@pytest.mark.parametrize("position", ["root", "local", "both"])
def test_hitmap_json_writes_actual_image(images, tmp_path, mode, position):
    # Arrange
    original, reproduced = images
    output = tmp_path / "hitmap.png"
    args = ["show-hitmap", str(original), str(reproduced), "-o", str(output),
            "--mode", mode, "--no-bbox"]
    variants = {"root": ["--json", *args], "local": [*args, "--json"],
                "both": ["--json", *args, "--json"]}
    # Act
    result = CliRunner().invoke(main, variants[position])
    data = json.loads(result.stdout)
    with Image.open(output) as rendered:
        size = rendered.size
    # Assert
    assert (result.exit_code, data["output"], data["mode"],
            data["stats"]["mismatch_pixels"], data["stats"]["mse"], size) == (
                0, str(output), mode, 1, 650.25, (10, 10),
            )


def test_hitmap_text_remains_available(images, tmp_path):
    # Arrange
    original, reproduced = images
    args = ["show-hitmap", str(original), str(reproduced), "-o", str(tmp_path / "text.png")]
    # Act
    result = CliRunner().invoke(main, args)
    # Assert
    assert (result.exit_code, "Hitmap saved:" in result.stdout) == (0, True)


def test_hitmap_missing_input_is_usage_error(tmp_path):
    # Arrange
    missing = str(tmp_path / "missing.png")
    # Act
    result = CliRunner().invoke(main, ["--json", "show-hitmap", missing, missing])
    # Assert
    assert result.exit_code == 2
