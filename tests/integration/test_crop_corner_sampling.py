"""Corner-derived padding stays pixel-faithful without a dense NumPy copy."""

import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, PngImagePlugin

from figrecipe._utils._crop import crop


def _image(path, mode):
    image = Image.new(mode, (7, 5))
    values = {
        "RGB": [(12, 34, 56), (78, 90, 123), (210, 240, 18), (254, 201, 234)],
        "RGBA": [(12, 34, 56, 0), (78, 90, 123, 64), (210, 240, 18, 255), (254, 201, 234, 128)],
        "LA": [(0, 0), (10, 255), (12, 64), (255, 128)],
        "L": [0, 100, 101, 255], "P": [0, 100, 101, 255],
        "1": [0, 0, 255, 255], "I": [-2147483648, 2147483647, -1, 0],
        "F": [1.99999988, 1.99999988, 2.0, 2.00000024],
    }
    for xy, value in zip([(0, 0), (6, 0), (0, 4), (6, 4)], values[mode]):
        image.putpixel(xy, value)
    image.save(path)
    return path


def _expected_padding(path):
    with Image.open(path) as image:
        data = np.array(image)
        samples = [data[0, 0], data[0, -1], data[-1, 0], data[-1, -1]]
        if data.ndim == 3:
            background = tuple(int(v) for v in np.median(samples, axis=0).astype(np.uint8))
        else:
            background = int(np.median(samples))
        expected = Image.new(image.mode, (12, 8), background)
        expected.paste(image, (2, 1))
        return expected.mode, expected.size, expected.tobytes()


@pytest.mark.parametrize("mode", ["RGB", "RGBA", "LA", "L", "P", "1", "I", "F"])
def test_extended_crop_matches_full_raster_reference(tmp_path, mode):
    # Arrange
    original = _image(tmp_path / "source.tiff", mode)
    expected = _expected_padding(original)
    output = tmp_path / "out.tiff"
    # Act
    crop(original, output_path=output, crop_box=(-2, -1, 10, 7))
    with Image.open(output) as image:
        actual = (image.mode, image.size, image.tobytes())
    # Assert
    assert actual == expected


_MEMORY_PROBE = r"""
import inspect, json, sys, tracemalloc
from pathlib import Path
from PIL import Image
from figrecipe._utils._crop import crop
assert Path(inspect.getfile(crop)).resolve() == Path(sys.argv[1])
original, output = Path(sys.argv[2]), Path(sys.argv[3])
warm = output.with_name("warm-input.png")
Image.new("RGB", (2, 2), "white").save(warm)
crop(warm, output_path=output.with_name("warm-output.png"), crop_box=(-1, -1, 3, 3))
tracemalloc.start()
crop(original, output_path=output, crop_box=(-1, -1, 1025, 769))
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(json.dumps({"peak_traced_bytes": peak}))
"""


def test_padding_background_avoids_dense_numpy_image_copy(tmp_path):
    # Arrange
    original = tmp_path / "large.png"
    Image.new("RGB", (1024, 768), "white").save(original)
    module = str(Path(inspect.getfile(crop)).resolve())
    # Act
    result = subprocess.run(
        [sys.executable, "-c", _MEMORY_PROBE, module, str(original), str(tmp_path / "padded.png")],
        capture_output=True, text=True, check=True, timeout=30,
    )
    observed = json.loads(result.stdout)
    # Assert
    assert observed["peak_traced_bytes"] < 1024 * 768 * 3, observed


def test_in_place_padding_preserves_png_metadata_and_offsets(tmp_path):
    # Arrange
    original = tmp_path / "metadata.png"
    info = PngImagePlugin.PngInfo()
    provenance = json.dumps({"source": "owned-fixture", "values": [1, 2]})
    info.add_text("provenance", provenance)
    Image.new("RGBA", (7, 5), (20, 40, 60, 128)).save(original, dpi=(300, 300), pnginfo=info)
    with Image.open(original) as image:
        original_dpi = image.info["dpi"]
    # Act
    path, offset = crop(original, output_path=original, crop_box=(-2, -1, 10, 7), return_offset=True)
    with Image.open(path) as image:
        actual = (image.info["dpi"], image.info["provenance"], image.size)
    # Assert
    assert (actual, offset) == (
        (original_dpi, provenance, (12, 8)),
        {"left": -2, "upper": -1, "right": 10, "lower": 7,
         "original_width": 7, "original_height": 5, "new_width": 12, "new_height": 8},
    )
