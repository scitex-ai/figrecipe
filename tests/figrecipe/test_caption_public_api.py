#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public API surface check for caption helpers (card: caption-public-api)."""


def test_caption_helpers_exposed_on_public_api():
    # Arrange
    import figrecipe as fr

    # Act
    exposed = [
        getattr(fr, "add_figure_caption", None),
        getattr(fr, "add_panel_captions", None),
        getattr(fr, "panel_label", None),
    ]

    # Assert
    assert all(callable(s) for s in exposed)

# EOF
