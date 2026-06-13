#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compose(caption=...) attaches caption to composed figure record.

Card: compose-caption-kwarg.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr


def test_compose_caption_kwarg_persists_on_record(tmp_path):
    # Arrange
    fig1, ax1 = fr.subplots()
    ax1.plot([1, 2, 3], [1, 4, 9], id="line1")
    recipe1 = tmp_path / "fig1.yaml"
    fr.save(fig1, recipe1, validate=False, verbose=False)

    fig2, ax2 = fr.subplots()
    ax2.bar([1, 2, 3], [3, 1, 4], id="bar1")
    recipe2 = tmp_path / "fig2.yaml"
    fr.save(fig2, recipe2, validate=False, verbose=False)

    # Act
    composed, _ = fr.compose(
        layout=(1, 2),
        sources={(0, 0): recipe1, (0, 1): recipe2},
        caption="Combined plot of line and bar.",
    )

    # Assert
    assert composed.record.caption == "Combined plot of line and bar."

# EOF
