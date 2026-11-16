#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Declared figure sources for clew's level-2 minimal slice.

A figure rebuilt by ``fr.reproduce(recipe)`` is derived from exactly the
files figrecipe read to rebuild it (recipe YAML + its data files). Any
change to the figure after that -- a new plot call, a decoration -- may
carry in-memory data, so the declaration is withdrawn. A figure built from
in-memory arrays is never declared. Real figures, real files, no mocks.
"""

import os

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402

import figrecipe as fr  # noqa: E402
from figrecipe._serializer._clew import (  # noqa: E402
    collecting_inputs,
    declaring,
    record_input,
)
from figrecipe._serializer._derived_sources import declared_sources  # noqa: E402


def _saved_recipe(tmp_path):
    fig, ax = fr.subplots()
    x = np.linspace(0, 1, 50)
    ax.plot(x, x**2, id="curve")
    ax.set_xlabel("x")
    image, yaml_path, _ = fr.save(
        fig, tmp_path / "fig.png", validate=False, verbose=False
    )
    return yaml_path


def _expected_sources(yaml_path):
    data_dir = yaml_path.parent / f"{yaml_path.stem}_data"
    data = sorted(os.path.realpath(p) for p in data_dir.iterdir())
    return [os.path.realpath(yaml_path)] + data


def test_reproduced_figure_declares_recipe_and_its_data(tmp_path):
    # Arrange
    yaml_path = _saved_recipe(tmp_path)
    fig, _ = fr.reproduce(yaml_path)
    # Act
    sources = declared_sources(fig)
    # Assert
    assert [sources[0]] + sorted(sources[1:]) == _expected_sources(yaml_path)


def test_new_plot_call_withdraws_the_declaration(tmp_path):
    # Arrange
    yaml_path = _saved_recipe(tmp_path)
    fig, ax = fr.reproduce(yaml_path)
    ax.plot([0, 1], [5, 6])  # in-memory data figrecipe cannot trace
    # Act
    sources = declared_sources(fig)
    # Assert
    assert sources is None


def test_new_decoration_withdraws_the_declaration(tmp_path):
    # Arrange
    yaml_path = _saved_recipe(tmp_path)
    fig, ax = fr.reproduce(yaml_path)
    ax.set_title("n=50")  # text may be computed from in-memory data
    # Act
    sources = declared_sources(fig)
    # Assert
    assert sources is None


def test_saving_does_not_withdraw_the_declaration(tmp_path):
    # Arrange: a save writes crop/layout geometry back into the record
    yaml_path = _saved_recipe(tmp_path)
    fig, _ = fr.reproduce(yaml_path)
    before = declared_sources(fig)
    fr.save(fig, tmp_path / "again.png", validate=False, verbose=False)
    # Act
    after = declared_sources(fig)
    # Assert
    assert after == before


def test_in_memory_figure_is_never_declared():
    # Arrange
    fig, ax = fr.subplots()
    ax.plot([0, 1], [1, 2])
    # Act
    sources = declared_sources(fig)
    # Assert
    assert sources is None


def test_collecting_inputs_sees_every_recorded_read(tmp_path):
    # Arrange
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("1\n")
    b.write_text("2\n")
    # Act
    with collecting_inputs() as seen:
        record_input(a)
        record_input(b)
        record_input(a)
    # Assert
    assert seen == [os.path.realpath(a), os.path.realpath(b)]


def test_reads_outside_a_collector_are_not_collected(tmp_path):
    # Arrange
    a = tmp_path / "a.csv"
    a.write_text("1\n")
    with collecting_inputs() as seen:
        pass
    # Act
    record_input(a)
    # Assert
    assert seen == []


def test_declaring_scope_is_restored_after_the_block():
    # Arrange
    from figrecipe._serializer._clew import _DECLARED

    # Act
    with declaring(["/x"]):
        inside = _DECLARED.get()
    # Assert
    assert (inside, _DECLARED.get()) == (("/x",), None)


# EOF
