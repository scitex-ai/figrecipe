"""GH #139: verify Diagram.render(ax) records a "diagram" CallRecord.

The bug: when a user calls ``Diagram.render(ax)`` directly on a
figrecipe-recording axes (the common path — most figrecipe paper figures
do this), the recipe ends up with NO record of the diagram render. On
``fr.save(fig, validate=True)`` the reproducer renders an empty panel
where the diagram should be, blows past the MSE threshold, and the
validator raises. This violates the figrecipe round-trip concept.

The fix lives in ``figrecipe._diagram._diagram._core.Diagram.render``:
after the matplotlib primitives are drawn, fire
``_wrappers/_axes_diagram::_record_diagram_call`` so the figure_record
gets a single high-level ``CallRecord(function="diagram",
kwargs={"diagram_data": diagram.to_dict()})`` that the reproducer's
existing ``replay_diagram_native_call`` already knows how to replay.

Each test focuses on a single observable property of that recording
hook (one assertion per test, AAA-structured) to satisfy STX-TQ002 /
STX-TQ007.
"""

from __future__ import annotations

import pytest


def _make_recording_fig_ax():
    """Real fr-wrapped figure + axes wired to a fresh Recorder.

    `fr.subplots` takes per-axes sizing in mm (`axes_width_mm` /
    `axes_height_mm`), NOT a Matplotlib-style `figsize_mm` tuple — the
    earlier copy-paste from the issue body used a fictional kwarg.
    """
    import matplotlib

    matplotlib.use("Agg")
    import figrecipe as fr

    return fr.subplots(axes_width_mm=80, axes_height_mm=60)


def _build_and_render_diagram(ax):
    """Build a minimal two-box Diagram and render it onto ``ax``."""
    from figrecipe.diagram import Diagram

    diag = Diagram(title="GH139 smoke", width_mm=80, height_mm=60)
    diag.add_box("a", "A", x_mm=5, y_mm=5)
    diag.add_box("b", "B", x_mm=40, y_mm=5)
    diag.add_arrow("a", "b")
    diag.render(ax)
    return diag


def test_render_appends_exactly_one_diagram_call_record():
    # Arrange
    pytest.importorskip("figrecipe")
    _, ax = _make_recording_fig_ax()
    # Act
    _build_and_render_diagram(ax)
    ax_record = ax._recorder.figure_record.get_or_create_axes(*ax._position)
    diagram_calls = [c for c in ax_record.calls if c.function == "diagram"]
    # Assert
    assert len(diagram_calls) == 1


def test_recorded_diagram_call_carries_diagram_data_kwarg():
    # Arrange
    pytest.importorskip("figrecipe")
    _, ax = _make_recording_fig_ax()
    _build_and_render_diagram(ax)
    ax_record = ax._recorder.figure_record.get_or_create_axes(*ax._position)
    # Act
    rec = next(c for c in ax_record.calls if c.function == "diagram")
    # Assert
    assert "diagram_data" in rec.kwargs


def test_recorded_diagram_data_round_trips_through_from_dict():
    # Arrange
    pytest.importorskip("figrecipe")
    from figrecipe.diagram import Diagram

    _, ax = _make_recording_fig_ax()
    _build_and_render_diagram(ax)
    ax_record = ax._recorder.figure_record.get_or_create_axes(*ax._position)
    rec = next(c for c in ax_record.calls if c.function == "diagram")
    # Act
    rebuilt = Diagram.from_dict(rec.kwargs["diagram_data"])
    # Assert
    assert rebuilt.title == "GH139 smoke"


def test_render_on_plain_mpl_axes_does_not_raise():
    # Arrange
    pytest.importorskip("figrecipe")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from figrecipe.diagram import Diagram

    _, ax = plt.subplots(figsize=(3, 2))
    diag = Diagram(title="GH139 noop", width_mm=80, height_mm=60)
    diag.add_box("only", "Only", x_mm=5, y_mm=5)
    # Act
    diag.render(ax)
    # Assert
    assert not hasattr(ax, "_recorder")
