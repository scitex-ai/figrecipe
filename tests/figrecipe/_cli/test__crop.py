"""Real-file controls for the crop CLI's margin parsing and input safety."""

import pytest
from click.testing import CliRunner
from PIL import Image

from figrecipe._cli._crop import crop


@pytest.mark.parametrize("margin", ["badmm", "badpx", "mm", "px", "1.2px", "bad"])
@pytest.mark.parametrize("options", [[], ["--overwrite"]])
def test_invalid_margin_reports_click_error_without_writing(tmp_path, margin, options):
    # Arrange
    source = tmp_path / "figure.png"
    Image.new("RGB", (20, 20), "white").save(source)
    original = source.read_bytes()
    arguments = [str(source), "--margin", margin, *options]
    # Act
    result = CliRunner().invoke(crop, arguments)
    # Assert
    assert {
        "exit": result.exit_code,
        "message": result.output,
        "raw_value_error": isinstance(result.exception, ValueError),
        "input": source.read_bytes(),
        "files": list(tmp_path.iterdir()),
    } == {
        "exit": 1,
        "message": f"Error: Invalid margin format: {margin}\n",
        "raw_value_error": False,
        "input": original,
        "files": [source],
    }



@pytest.mark.parametrize("margin,side", [("2px", 14), ("2mm", 58), ("0", 10)])
def test_valid_margin_crops_actual_pixels_and_preserves_input(tmp_path, margin, side):
    # Arrange
    source = tmp_path / "figure.png"
    image = Image.new("RGB", (20, 20), "white")
    image.paste((0, 0, 0), (5, 5, 15, 15))
    image.save(source, dpi=(300, 300))
    original = source.read_bytes()
    output = tmp_path / "figure_cropped.png"
    expected = Image.new("RGB", (side, side), "white")
    padding = (side - 10) // 2
    expected.paste((0, 0, 0), (padding, padding, padding + 10, padding + 10))
    # Act
    result = CliRunner().invoke(crop, [str(source), "--margin", margin])
    # Assert
    with Image.open(output) as actual:
        dimensions, pixels = actual.size, actual.tobytes()
    assert {
        "exit": result.exit_code,
        "message": result.output,
        "dimensions": dimensions,
        "pixels": pixels,
        "input": source.read_bytes(),
    } == {
        "exit": 0,
        "message": f"Cropped: {output}\n",
        "dimensions": expected.size,
        "pixels": expected.tobytes(),
        "input": original,
    }
