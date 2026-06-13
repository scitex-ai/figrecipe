#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caption persists in FigureRecord (card: persist-caption-roundtrip [P1]).

After `add_figure_caption(fig, text)`, the caption must be visible on the
FigureRecord so it survives a save -> reproduce roundtrip (i.e. it lands in
the serialized recipe's metadata.caption field).
"""


def test_add_figure_caption_persists_on_figure_record():
    # Arrange
    import figrecipe as fr
    from figrecipe._captions import add_figure_caption

    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])

    # Act
    add_figure_caption(fig, "Quadratic growth example.")

    # Assert
    assert fig._recorder.figure_record.caption == "Quadratic growth example."

# EOF
