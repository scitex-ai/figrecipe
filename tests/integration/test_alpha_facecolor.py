"""Explicit RGBA backgrounds retain their alpha during real PNG exports."""

from PIL import Image
import pytest

import figrecipe as fr
from figrecipe._api._save_config import _is_opaque_facecolor


@pytest.mark.parametrize("color", ["#ffffff00", "#fff0", (1, 1, 1, 0),
                                  "#12345680", (0.1, 0.2, 0.3, 0.5),
                                  None, "none", "transparent"])
def test_alpha_colors_are_not_classified_as_opaque(color):
    # Arrange
    requested = color
    # Act
    actual = _is_opaque_facecolor(requested)
    # Assert
    assert actual is False


@pytest.mark.parametrize("color", ["white", "#fff", "#123456ff", (1, 1, 1),
                                  (1, 1, 1, 1), "0.5", "auto"])
def test_opaque_colors_still_override_patch_alpha(color):
    # Arrange
    requested = color
    # Act
    actual = _is_opaque_facecolor(requested)
    # Assert
    assert actual is True


@pytest.mark.parametrize("color,alpha", [("#ffffff00", 0), ("#fff0", 0),
                                        ("#12345680", 128),
                                        ((0.1, 0.2, 0.3, 0.5), 128),
                                        ("#123456", 255), ("auto", 255)])
@pytest.mark.parametrize("crop", [False, True])
def test_saved_png_keeps_requested_background_alpha(tmp_path, color, alpha, crop):
    # Arrange
    layout = dict(axes_width_mm=40, axes_height_mm=25,
                  margin_left_mm=2, margin_right_mm=2,
                  margin_top_mm=2, margin_bottom_mm=2) if crop else dict(figsize=(3, 2))
    fig, ax = fr.subplots(constrained_layout=False, **layout)
    ax.plot([0, 1], [0, 1], label="Outside")
    ax.legend(loc="upper left", bbox_to_anchor=(1.6, 1))
    before = (fig.fig.patch.get_alpha(), ax.ax.patch.get_alpha())
    # Act
    image, _, result = fr.save(fig, tmp_path / "alpha.png", facecolor=color,
                               dpi=100, verbose=False)
    actual = Image.open(image).convert("RGBA").getpixel((0, 0))[3]
    after = (fig.fig.patch.get_alpha(), ax.ax.patch.get_alpha())
    # Assert
    assert (actual, after, result.valid, result.mse) == (alpha, before, True, 0.0)


def test_opaque_save_restores_explicit_patch_alpha(tmp_path):
    # Arrange
    fig, ax = fr.subplots(figsize=(3, 2), constrained_layout=False)
    ax.plot([0, 1], [0, 1])
    fig.fig.patch.set_alpha(0.25)
    ax.ax.patch.set_alpha(0.4)
    # Act
    fr.save(fig, tmp_path / "image.png", facecolor="white", dpi=100, verbose=False)
    actual = (fig.fig.patch.get_alpha(), ax.ax.patch.get_alpha())
    # Assert
    assert actual == (0.25, 0.4)


def test_failed_opaque_save_restores_explicit_patch_alpha(tmp_path):
    # Arrange
    fig, ax = fr.subplots(figsize=(3, 2), constrained_layout=False)
    fig.fig.patch.set_alpha(0.25)
    ax.ax.patch.set_alpha(0.4)
    error = None
    # Act
    try:
        fr.save(fig, tmp_path / "absent" / "image.png", facecolor="white",
                dpi=100, verbose=False)
    except FileNotFoundError as exc:
        error = type(exc)
    actual = (fig.fig.patch.get_alpha(), ax.ax.patch.get_alpha())
    # Assert
    assert (error, actual) == (FileNotFoundError, (0.25, 0.4))


def test_invalid_color_keeps_matplotlib_error(tmp_path):
    # Arrange
    fig, _ = fr.subplots(figsize=(3, 2), constrained_layout=False)
    target = tmp_path / "invalid.png"
    # Act
    # Assert
    with pytest.raises(ValueError, match="RGBA"):
        fr.save(fig, target, facecolor="invalid-color", verbose=False)
