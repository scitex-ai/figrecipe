"""Requested all-content crops must render overflow, not pad missing ink."""

from PIL import Image
import numpy as np
import pytest

import figrecipe as fr


def overflow_figure():
    """Put an entire magenta legend beyond the original physical canvas."""
    fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=25,
                          margin_left_mm=2, margin_right_mm=2,
                          margin_top_mm=2, margin_bottom_mm=2,
                          constrained_layout=False)
    ax.plot([0, 1, 2], [0, 1, 3], label="Entire outside legend text END")
    ax.legend(loc="upper left", bbox_to_anchor=(1.6, 1),
              labelcolor="#ff00ff", edgecolor="#ff00ff")
    fig.canvas.draw()
    return fig, ax


def test_all_content_crop_contains_actual_outside_legend_ink(tmp_path):
    # Arrange
    fig, ax = overflow_figure()
    outside = ax.ax.get_legend().get_window_extent().x0 > fig.fig.bbox.x1
    # Act
    image, _, result = fr.save(fig, tmp_path / "outside.png", verbose=False, dpi=150)
    rgb = np.asarray(Image.open(image).convert("RGB"))
    magenta = (rgb[..., 0] > 200) & (rgb[..., 1] < 80) & (rgb[..., 2] > 200)
    rightmost = np.max(np.where(magenta)[1], initial=-1)
    # Assert
    assert (outside, result.valid, int(magenta.sum()) > 100,
            rgb.shape[1] - 1 - rightmost > 5) == (True, True, True, True)


def test_cropped_overflow_replays_pixel_exactly(tmp_path):
    # Arrange
    fig, _ = overflow_figure()
    # Act
    _, _, result = fr.save(fig, tmp_path / "replay.png", verbose=False, dpi=150)
    # Assert
    assert (result.valid, result.mse) == (True, 0.0)


def test_overflow_export_preserves_physical_axes_width(tmp_path):
    # Arrange
    fig, ax = overflow_figure()
    expected = ax.ax.get_window_extent().width / fig.fig.dpi * 25.4
    # Act
    image, _, _ = fr.save(fig, tmp_path / "physical.png", verbose=False, dpi=150)
    width = Image.open(image).width
    actual = next(iter(fig.record.axes.values())).bbox[2] * width / 150 * 25.4
    # Assert
    assert actual == pytest.approx(expected, abs=25.4 / 150)


def test_fixed_canvas_export_without_requested_crop_keeps_its_size(tmp_path):
    # Arrange
    fig, ax = fr.subplots(figsize=(3, 2), constrained_layout=False)
    ax.plot([0, 1], [0, 1], label="Fixed canvas outside label")
    ax.legend(loc="upper left", bbox_to_anchor=(2, 1))
    expected = tuple(round(v * 150) for v in fig.fig.get_size_inches())
    # Act
    image, _, _ = fr.save(fig, tmp_path / "fixed.png", verbose=False, dpi=150)
    actual = Image.open(image).size
    # Assert
    assert actual == expected


def test_overflow_hitmap_uses_the_same_output_extent(tmp_path):
    # Arrange
    fig, _ = overflow_figure()
    # Act
    image, _, _ = fr.save(fig, tmp_path / "hitmap.png", verbose=False,
                          dpi=150, save_hitmap=True)
    with Image.open(image) as main, Image.open(tmp_path / "hitmap_hitmap.png") as ids:
        sizes = (main.size, ids.size)
    # Assert
    assert sizes[0] == sizes[1]


def test_explicit_hitmap_bbox_keeps_existing_pixel_budget():
    # Arrange
    from matplotlib.transforms import Bbox
    from figrecipe._editor._hitmap import generate_hitmap
    fig, ax = fr.subplots(figsize=(3, 2), constrained_layout=False)
    ax.plot([0, 1], [0, 1])
    # Act
    image, _ = generate_hitmap(fig.fig, dpi=150,
                              bbox_inches=Bbox.from_bounds(0, 0, 25, 1))
    # Assert
    assert max(image.size) <= 2000


@pytest.mark.parametrize("extra_draws", [0, 5, 15])
def test_overflow_export_is_pixel_exact_after_extra_replay_draws(tmp_path, extra_draws):
    # Arrange
    fig, _ = overflow_figure()
    image, recipe, _ = fr.save(fig, tmp_path / "original.png", verbose=False, dpi=150)
    expected = np.asarray(Image.open(image).convert("RGBA"))
    replay, _ = fr.reproduce(recipe)
    for _ in range(extra_draws):
        replay.canvas.draw()
    # Act
    output, _, _ = fr.save(replay, tmp_path / "again.png", verbose=False, dpi=150)
    actual = np.asarray(Image.open(output).convert("RGBA"))
    # Assert
    assert np.array_equal(actual, expected)


def test_opaque_background_is_preserved_for_overflow_render(tmp_path):
    # Arrange
    fig, _ = overflow_figure()
    # Act
    image, _, _ = fr.save(fig, tmp_path / "opaque.png", verbose=False,
                          dpi=150, facecolor="#123456")
    actual = Image.open(image).convert("RGBA").getpixel((0, 0))
    # Assert
    assert actual == (18, 52, 86, 255)


def test_transparent_background_is_preserved_for_overflow_render(tmp_path):
    # Arrange
    fig, _ = overflow_figure()
    # Act
    image, _, _ = fr.save(fig, tmp_path / "transparent.png", verbose=False,
                          dpi=150, facecolor="none")
    actual = Image.open(image).convert("RGBA").getpixel((0, 0))
    # Assert
    assert actual[3] == 0
