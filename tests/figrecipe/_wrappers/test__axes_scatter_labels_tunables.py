"""scatter_labels must forward the solver's tunables — and change nothing without them.

Carried from figrecipe-declutter-followups-20260714 item 2: solve_label_positions
accepts step / max_radius / ink_tol, scatter_labels called it positionally with
defaults and never exposed them, while stx_annotate_n already forwarded two of the
three. The asymmetry was arbitrary, and a crowded panel had no knob short of
calling the private solver.

THE FIRST TEST IS THE IMPORTANT ONE. Parameter plumbing is the kind of change that
can look right while doing nothing, so this file proves the knobs are LIVE (a
different step moves labels) as well as INERT when unset (identical placement).
Without the live check, a forwarding bug would pass every other test here.
"""

from __future__ import annotations

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

import figrecipe as fr


def _placed(**kwargs):
    """Label positions after a deterministic 14-point scatter."""
    fig, ax = fr.subplots()
    rng = np.random.default_rng(7)
    x, y = rng.random(14), rng.random(14)
    ax.scatter(x, y, id="pts")
    ax.scatter_labels(x, y, [f"L{i}" for i in range(14)], id="labs", **kwargs)
    fig.fig.canvas.draw()
    return [
        tuple(round(v, 4) for v in t.get_position())
        for t in ax.axes.texts
        if t.get_text().startswith("L")
    ]


# ---------------------------------------------------------------------------
# the knobs must be LIVE
# ---------------------------------------------------------------------------


def test_a_different_step_moves_the_labels():
    # Arrange: if forwarding were broken this would silently pass everything
    # else in this file, so it is checked first.
    tight = _placed(step=4.0)
    # Act
    loose = _placed(step=40.0)
    # Assert
    assert loose != tight


def test_max_radius_is_accepted():
    # Arrange
    kwargs = {"max_radius": 40.0}
    # Act
    placed = _placed(**kwargs)
    # Assert
    assert len(placed) == 14


def test_ink_tol_is_accepted():
    # Arrange
    kwargs = {"ink_tol": 0.25}
    # Act
    placed = _placed(**kwargs)
    # Assert
    assert len(placed) == 14


def test_all_three_together_are_accepted():
    # Arrange
    kwargs = {"step": 11.0, "max_radius": 44.0, "ink_tol": 0.25}
    # Act
    placed = _placed(**kwargs)
    # Assert
    assert len(placed) == 14


# ---------------------------------------------------------------------------
# ...and INERT when not passed
# ---------------------------------------------------------------------------


def test_omitting_the_tunables_is_deterministic():
    # Arrange: no kwargs are forwarded at all in this case, so the solver call is
    # identical to what it was before the tunables existed.
    first = _placed()
    # Act
    second = _placed()
    # Assert
    assert first == second


def test_passing_none_matches_omitting():
    # Arrange: None means "use the solver's default", so it must be
    # indistinguishable from not passing the argument.
    omitted = _placed()
    # Act
    explicit_none = _placed(step=None, max_radius=None, ink_tol=None)
    # Assert
    assert explicit_none == omitted


def test_the_signature_does_not_restate_the_solver_defaults():
    # Arrange: restating 6.0/160.0 here would create a second place to change,
    # which is the defect this forwarding style avoids. The default must be None.
    import inspect

    sig = inspect.signature(fr.subplots()[1].scatter_labels)
    # Act
    defaults = {n: p.default for n, p in sig.parameters.items() if n in
                ("step", "max_radius", "ink_tol")}
    # Assert
    assert defaults == {"step": None, "max_radius": None, "ink_tol": None}


def test_every_tunable_is_exposed():
    # Arrange: the solver's kw-only knobs and what scatter_labels offers must not
    # drift apart again.
    import inspect

    from figrecipe._declutter import solve_label_positions

    solver_knobs = {
        n
        for n, p in inspect.signature(solve_label_positions).parameters.items()
        if p.kind is inspect.Parameter.KEYWORD_ONLY
    }
    # Act
    exposed = set(inspect.signature(fr.subplots()[1].scatter_labels).parameters)
    # Assert
    assert solver_knobs <= exposed
