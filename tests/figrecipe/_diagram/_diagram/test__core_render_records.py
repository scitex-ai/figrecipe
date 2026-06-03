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

These tests assert the recording side only. The replay side has its own
coverage under ``tests/figrecipe/_reproducer/test__replay_diagram.py``;
together they close the round-trip.
"""

from __future__ import annotations

import pytest


def _make_recording_axes():
    """Return a real fr-wrapped figure + axes wired to a fresh Recorder."""
    import matplotlib

    matplotlib.use("Agg")
    import figrecipe as fr

    fig, ax = fr.subplots(figsize_mm=(80, 60))
    return fig, ax


def test_render_on_recording_axes_appends_diagram_call_record():
    """Direct ``Diagram.render(ax)`` records the diagram for replay."""
    fr = pytest.importorskip("figrecipe")
    _make_recording_axes_fn = _make_recording_axes  # local alias for readability
    fig, ax = _make_recording_axes_fn()

    from figrecipe.diagram import Diagram

    diag = Diagram(title="GH139 smoke", width_mm=80, height_mm=60)
    diag.add_box("a", "A", x_mm=5, y_mm=5)
    diag.add_box("b", "B", x_mm=40, y_mm=5)
    diag.add_arrow("a", "b")
    diag.render(ax)

    # The recording axes carries a back-pointer to the Recorder; pluck it.
    recorder = getattr(ax, "_recorder", None)
    assert recorder is not None, "fr.subplots axes should expose ._recorder"

    fig_record = recorder.figure_record
    assert fig_record is not None
    ax_record = fig_record.get_or_create_axes(*ax._position)

    diagram_calls = [c for c in ax_record.calls if c.function == "diagram"]
    assert len(diagram_calls) == 1, (
        f"expected exactly one recorded diagram call, got {len(diagram_calls)}"
    )

    rec = diagram_calls[0]
    assert "diagram_data" in rec.kwargs, (
        "recorded diagram call must carry diagram_data for replay"
    )
    diagram_data = rec.kwargs["diagram_data"]
    assert isinstance(diagram_data, dict)
    # diagram_data must round-trip through Diagram.from_dict so the reproducer
    # can rebuild the renderer at replay time.
    rebuilt = Diagram.from_dict(diagram_data)
    assert rebuilt.title == "GH139 smoke"


def test_render_without_recording_axes_is_a_silent_noop():
    """``Diagram.render(ax)`` on a plain matplotlib axes must not raise."""
    pytest.importorskip("figrecipe")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from figrecipe.diagram import Diagram

    fig, ax = plt.subplots(figsize=(3, 2))
    # Plain axes has no ._recorder / ._position; the recording branch
    # should short-circuit without raising and without polluting the
    # bare matplotlib axes object.
    diag = Diagram(title="GH139 noop", width_mm=80, height_mm=60)
    diag.add_box("only", "Only", x_mm=5, y_mm=5)
    diag.render(ax)  # must not raise
    assert not hasattr(ax, "_recorder")
