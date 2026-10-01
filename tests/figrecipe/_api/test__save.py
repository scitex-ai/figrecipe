"""Half-save safety for the image+recipe pair (src<->tests mirror for _api._save).

A figure save declares a pair (image + recipe). If the recipe write fails after
the image is already on disk, the caller would be left with an image and no
recipe to replay it -- a half-saved figure that "looks" saved. These tests pin
the post-condition of that failure. Each test asserts exactly one filesystem
state (STX-TQ007); the shared figure/poison/save setup is module-level
non-test helpers below so no test function carries more than one assertion.

Also covers save-time figsize/dpi refresh (card figrecipe-set-size-inches-
after-subplots-size-mismatch-20260906): the record is seeded from the live
figure at creation, so a figure that never resizes stays byte-identical, while
fig.set_size_inches(...) (delegated, never recorded as a call) must reach the
recipe or the replay is built at the wrong size and validation has nothing to
compare.
"""

import matplotlib

matplotlib.use("Agg")

from typing import Any, Optional, Tuple

import pytest

import figrecipe as fr
from figrecipe._api import _save


def test_import__api__save_module():
    # Arrange
    module_path = "figrecipe._api._save"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# --- Shared setup (module-level, NOT test functions) -------------------------


def make_figure() -> Any:
    """A real ``RecordingFigure`` with one plotted series, drawn once."""
    fig, ax = fr.subplots(1, 1, axes_width_mm=60, axes_height_mm=40)
    ax.plot([0, 1, 2], [0, 1, 4])
    fig._fig.canvas.draw()
    return fig


def poison_recipe_write(fig: Any) -> Any:
    """Make the recipe write genuinely fail with a ``RepresenterError``.

    A ``frozenset`` is not YAML-representable and is serialized into the
    top-level ``id`` field, which the save pipeline never converts or strips --
    so ``yaml.dump`` raises mid-write. No monkeypatch: this is real record
    content, the same failure shape PR #374 fixed for CapStyle generalised to
    any future serialization failure.
    """
    fig._recorder.figure_record.id = frozenset([1, 2])
    return fig


def attempt_save(fig: Any, target: str) -> Tuple[Optional[BaseException], Any]:
    """Run ``savefig``; return (exception-or-None, save-return-value)."""
    try:
        return None, fig.savefig(target, validate=False, verbose=False)
    except Exception as exc:  # noqa: BLE001 -- the test's subject is the raise
        return exc, None


# --- The half-save post-conditions -----------------------------------------


def test_recipe_write_failure_removes_the_image_it_created(tmp_path):
    # Arrange: poison the record so save_recipe raises a RepresenterError mid-write.
    fig = poison_recipe_write(make_figure())
    target = str(tmp_path / "half.png")
    # Act
    attempt_save(fig, target)
    # Assert: the image this save wrote is gone -- no image-without-recipe pair.
    assert not (tmp_path / "half.png").exists()


def test_recipe_write_failure_keeps_a_preexisting_image(tmp_path):
    # Arrange: a user's older figure already exists at the target path.
    existing = tmp_path / "keep.png"
    existing.write_bytes(b"prior-user-figure-bytes")
    fig = poison_recipe_write(make_figure())
    # Act
    attempt_save(fig, str(existing))
    # Assert: the pre-existing image is KEPT -- the save overwrote it with its
    # render but must not then delete it (that would empty the user's path).
    assert existing.exists()


def test_recipe_write_failure_removes_the_data_sidecar_dir(tmp_path):
    # Arrange
    fig = poison_recipe_write(make_figure())
    target = str(tmp_path / "sided.png")
    # Act
    attempt_save(fig, target)
    # Assert: the data sidecar dir the serializer created before the yaml failure
    # is rolled back too (an orphaned <stem>_data/ with no recipe is a half-pair).
    assert not (tmp_path / "sided_data").exists()


def test_recipe_write_success_leaves_the_pair(tmp_path):
    # Arrange: a clean (unpoisoned) figure -- the guard must not break the happy path.
    fig = make_figure()
    target = str(tmp_path / "ok.png")
    # Act
    attempt_save(fig, target)
    # Assert: both image and recipe exist (a successful save is untouched).
    assert (tmp_path / "ok.png").exists() and (tmp_path / "ok.yaml").exists()


def test_rollback_helper_removes_fresh_image(tmp_path):
    # Arrange: a fresh image this save created (pre_existing False).
    img = tmp_path / "u.png"
    img.write_bytes(b"fresh-image")
    data_dir = tmp_path / "u_data"
    data_dir.mkdir()
    # Act
    removed_img = _save._roll_back_image_side_on_recipe_failure(
        img,
        tmp_path / "u.yaml",
        data_dir,
        None,
        {img: False, data_dir: False},
    )
    # Assert: the helper reports it removed the image (its create-only contract).
    assert removed_img is True


def test_rollback_helper_keeps_preexisting_yaml(tmp_path):
    # Arrange: a yaml that pre-existed from an earlier save.
    img = tmp_path / "v.png"
    yaml_p = tmp_path / "v.yaml"
    data_dir = tmp_path / "v_data"
    img.write_bytes(b"fresh-image")
    data_dir.mkdir()
    yaml_p.write_text("old-recipe")
    # Act
    _save._roll_back_image_side_on_recipe_failure(
        img,
        yaml_p,
        data_dir,
        None,
        {img: False, data_dir: False},
    )
    # Assert: the pre-existing yaml is untouched (atomic write -> never a half yaml).
    assert yaml_p.read_text() == "old-recipe"


def test_rollback_helper_removes_orphaned_data_dir(tmp_path):
    # Arrange: a data sidecar dir created by the failed save.
    img = tmp_path / "w.png"
    data_dir = tmp_path / "w_data"
    img.write_bytes(b"fresh-image")
    data_dir.mkdir()
    (data_dir / "arr.csv").write_text("x\n1\n")
    # Act
    _save._roll_back_image_side_on_recipe_failure(
        img,
        tmp_path / "w.yaml",
        data_dir,
        None,
        {img: False, data_dir: False},
    )
    # Assert: the orphaned data sidecar dir is removed.
    assert not data_dir.exists()


# ── Save-time figsize/dpi refresh ────────────────────────────────────────────
#
# card figrecipe-set-size-inches-after-subplots-size-mismatch-20260906: the
# record is seeded from the live figure at creation, so fig.set_size_inches()
# (delegated to matplotlib, never recorded as a call) used to leave the recipe
# holding the ORIGINAL size while the saved PNG had the new one -- the replay
# is built at record.figsize, so validation had nothing to compare. The fix
# refreshes record.figsize/record.dpi from the live figure at save time.


def _save_and_reloaded_figsize(tmp_path, name):
    # Arrange: a plain 1x1 figure, optionally resized by the caller via the
    # returned (fig, target) pair before save.
    fig, ax = fr.subplots(1, 1, figsize=(8, 6), constrained_layout=False)
    ax.plot([0, 1, 2], [0, 1, 4])
    target = str(tmp_path / (name + ".png"))
    return fig, target


def test_resize_after_subplots_reaches_the_saved_recipe(tmp_path):
    # Arrange
    fig, target = _save_and_reloaded_figsize(tmp_path, "rs")
    fig.set_size_inches(6, 4)
    # Act
    fr.save(fig, target, validate=False, verbose=False)
    reloaded, _ = fr.reproduce(target)
    # Assert: the recipe carries the LIVE size (previously (8,6) -> size mismatch).
    assert tuple(reloaded.record.figsize) == (6.0, 4.0)


def test_dpi_change_after_subplots_reaches_the_saved_recipe(tmp_path):
    # Arrange
    fig, target = _save_and_reloaded_figsize(tmp_path, "dpi")
    fig.set_dpi(150)
    # Act
    fr.save(fig, target, validate=False, verbose=False)
    reloaded, _ = fr.reproduce(target)
    # Assert: the recipe carries the live dpi.
    assert reloaded.record.dpi == 150


def test_no_resize_keeps_creation_figsize_untouched(tmp_path):
    # Arrange: the control -- a figure that never resizes must save exactly the
    # creation-time values (byte-identical behaviour, per the card's requirement).
    fig, target = _save_and_reloaded_figsize(tmp_path, "ctl")
    # Act
    fr.save(fig, target, validate=False, verbose=False)
    reloaded, _ = fr.reproduce(target)
    # Assert
    assert tuple(reloaded.record.figsize) == (8.0, 6.0)
