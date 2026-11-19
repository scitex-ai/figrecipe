"""Recorded raster crops enclose content and the requested physical margins."""

from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from figrecipe._api._save_helpers import crop_to_content_bbox


def test_import__api__save_helpers_module():
    # Arrange
    module_path = "figrecipe._api._save_helpers"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _saved_image(path: Path):
    info = PngImagePlugin.PngInfo()
    info.add_text("provenance", "owned crop enclosure fixture")
    with Image.new("RGB", (100, 100), "white") as image:
        image.putpixel((50, 50), (0, 0, 0))
        image.save(path, dpi=(100, 100), pnginfo=info)
    return path


@pytest.mark.parametrize(
    "bbox,margins,dpi,expected",
    [
        # All four fractional edges lie outside their nearest integers.
        ([0.1075, 0.1075, 0.785, 0.785], (0, 0, 0, 0), 100, (10, 10, 90, 90)),
        # 0.1 mm needs 0.394/0.591/1.181 px at these output resolutions.
        ([0.2, 0.2, 0.6, 0.6], (0.1, 0.1, 0.1, 0.1), 100, (19, 19, 81, 81)),
        ([0.2, 0.2, 0.6, 0.6], (0.1, 0.1, 0.1, 0.1), 150, (19, 19, 81, 81)),
        ([0.2, 0.2, 0.6, 0.6], (0.1, 0.1, 0.1, 0.1), 300, (18, 18, 82, 82)),
        # Margins are independent, including Matplotlib's inverted y direction.
        ([0.2, 0.2, 0.6, 0.6], (0.1, 0.2, 0.3, 0.4), 100, (19, 18, 81, 82)),
        # Integral edges remain unchanged; overflow is padded, never clamped.
        ([0.25, 0.25, 0.5, 0.5], (0, 0, 0, 0), 100, (25, 25, 75, 75)),
        ([-0.0125, -0.0125, 1.025, 1.025], (0, 0, 0, 0), 100, (-2, -2, 102, 102)),
    ],
)
def test_recorded_crop_encloses_fractional_content_and_margin(
    tmp_path, bbox, margins, dpi, expected,
):
    # Arrange
    path = _saved_image(tmp_path / "enclosed.png")
    sides = dict(zip(["left", "right", "top", "bottom"], margins))
    # Act
    offset = crop_to_content_bbox(path, bbox, sides, dpi)
    with Image.open(path) as image:
        actual = (offset["left"], offset["upper"], offset["right"], offset["lower"])
        size = image.size
        provenance = image.info["provenance"]
    # Assert
    assert (actual, size, provenance) == (
        expected, (expected[2] - expected[0], expected[3] - expected[1]),
        "owned crop enclosure fixture",
    )
