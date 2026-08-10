"""``create_axes_with_size_mm`` must deliver the mm it was asked for.

WHY THIS FILE EXISTS. ``_dimension_viewer`` imported this helper from
``._figure_from_axes_mm`` — a module that was never migrated into figrecipe
(``git log --all`` finds no trace of it) — so BOTH public functions in that module
raised ModuleNotFoundError on every call, and had since the figrecipe-owns-plt
migration. Nothing caught it because the imports sit INSIDE the function bodies:
the module imports cleanly, ``import figrecipe`` is unaffected, the import-smoke CI
leg passes, and the auto-generated mirror test uses ``pytest.importorskip``, which
SKIPS. A public export was dead for weeks with 2738 tests green.

These are EXACT assertions. A 30mm axes has one correct rendered width, because
_api/_subplots.py states the arithmetic outright. See
figrecipe-rendered-axes-exceeds-requested-mm-by-a-constant-20260809 — the reason
this helper can exist at all is that ``constrained_layout=False`` keeps the mm
request from being discarded, which was only established on 2026-08-09.
"""

from __future__ import annotations

import matplotlib
import pytest

matplotlib.use("Agg")

from figrecipe._utils._dimension_info import (
    create_axes_with_size_mm,
    get_dimension_info,
)


def _axes_mm(fig, ax):
    """Rendered axes size in mm, measured after the canvas is drawn."""
    raw = fig.fig if hasattr(fig, "fig") else fig
    return get_dimension_info(raw, ax)["axes_size_mm"]


# ---------------------------------------------------------------------------
# publication mode: exactly what was asked for
# ---------------------------------------------------------------------------


def test_publication_mode_delivers_the_requested_width():
    # Arrange
    fig, ax = create_axes_with_size_mm(30, 21)
    # Act
    width_mm = _axes_mm(fig, ax)[0]
    # Assert
    assert width_mm == pytest.approx(30.0, abs=0.01)


def test_publication_mode_delivers_the_requested_height():
    # Arrange
    fig, ax = create_axes_with_size_mm(30, 21)
    # Act
    height_mm = _axes_mm(fig, ax)[1]
    # Assert
    assert height_mm == pytest.approx(21.0, abs=0.01)


def test_a_different_size_is_also_exact():
    # Arrange: guards against a hardcoded default passing the tests above.
    fig, ax = create_axes_with_size_mm(60, 20)
    # Act
    width_mm, height_mm = _axes_mm(fig, ax)
    # Assert
    assert (width_mm, height_mm) == pytest.approx((60.0, 20.0), abs=0.01)


def test_a_portrait_request_is_not_transposed():
    # Arrange
    fig, ax = create_axes_with_size_mm(20, 60)
    # Act
    width_mm, height_mm = _axes_mm(fig, ax)
    # Assert
    assert (width_mm, height_mm) == pytest.approx((20.0, 60.0), abs=0.01)


# ---------------------------------------------------------------------------
# display mode: 3x, so on-screen inspection is legible at the same proportions
# ---------------------------------------------------------------------------


def test_display_mode_scales_by_three():
    # Arrange
    fig, ax = create_axes_with_size_mm(30, 21, mode="display")
    # Act
    width_mm, height_mm = _axes_mm(fig, ax)
    # Assert
    assert (width_mm, height_mm) == pytest.approx((90.0, 63.0), abs=0.01)


def test_display_mode_preserves_the_aspect_ratio():
    # Arrange: scaling is only useful if the shape survives it.
    pub_w, pub_h = _axes_mm(*create_axes_with_size_mm(30, 21))
    disp_w, disp_h = _axes_mm(*create_axes_with_size_mm(30, 21, mode="display"))
    # Act
    same_shape = (disp_w / disp_h) == pytest.approx(pub_w / pub_h, abs=0.001)
    # Assert
    assert same_shape


# ---------------------------------------------------------------------------
# an unknown mode fails loud rather than picking one
# ---------------------------------------------------------------------------


def test_an_unknown_mode_raises():
    # Arrange
    bad_mode = "whatever"
    # Act
    act = lambda: create_axes_with_size_mm(30, 21, mode=bad_mode)  # noqa: E731
    # Assert
    with pytest.raises(ValueError):
        act()


def test_the_error_names_the_publication_mode():
    # Arrange: an error that does not say what to do instead is half-written.
    try:
        create_axes_with_size_mm(30, 21, mode="whatever")
        message = ""
    except ValueError as exc:
        message = str(exc)
    # Act
    names_it = "publication" in message
    # Assert
    assert names_it


def test_the_error_names_the_display_mode():
    # Arrange
    try:
        create_axes_with_size_mm(30, 21, mode="whatever")
        message = ""
    except ValueError as exc:
        message = str(exc)
    # Act
    names_it = "display" in message
    # Assert
    assert names_it


# ---------------------------------------------------------------------------
# the two public functions that were dead must actually RUN
# ---------------------------------------------------------------------------


def test_compare_modes_runs_and_writes_a_file(tmp_path):
    # Arrange: this raised ModuleNotFoundError on every call before 2026-08-09.
    from figrecipe._utils import compare_modes

    out = tmp_path / "cmp.png"
    # Act
    compare_modes(30, 21, output_path=str(out))
    # Assert
    assert out.exists()


def test_view_dimensions_runs_and_writes_a_file(tmp_path):
    # Arrange: same — dead on every call.
    from figrecipe._utils._dimension_viewer import view_dimensions

    fig, ax = create_axes_with_size_mm(30, 21)
    raw = fig.fig if hasattr(fig, "fig") else fig
    out = tmp_path / "dim.png"
    # Act
    view_dimensions(raw, ax, output_path=str(out))
    # Assert
    assert out.exists()
