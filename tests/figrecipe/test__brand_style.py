#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for brand-triggered global house-style application.

``FIGRECIPE_BRAND`` is read at import time, so brand-on/brand-off behaviour is
exercised in subprocesses with a clean interpreter and a fresh env.
"""

import json
import subprocess
import sys

import pytest

from figrecipe._brand_style import apply_brand_style


def _run(brand):
    """Import figrecipe in a subprocess with the given brand; return rcParams."""
    env_setup = ""
    if brand is not None:
        env_setup = (
            f"import os; os.environ['FIGRECIPE_BRAND'] = {brand!r}\n"
            "os.environ['FIGRECIPE_ALIAS'] = 'plt'\n"
        )
    code = (
        env_setup + "import matplotlib; matplotlib.use('Agg')\n"
        "import figrecipe\n"
        "import matplotlib as mpl\n"
        "import json\n"
        "cyc = mpl.rcParams['axes.prop_cycle'].by_key()['color']\n"
        "print(json.dumps({\n"
        "    'font_size': mpl.rcParams['font.size'],\n"
        "    'titlesize': mpl.rcParams['axes.titlesize'],\n"
        "    'labelsize': mpl.rcParams['axes.labelsize'],\n"
        "    'spines_top': mpl.rcParams['axes.spines.top'],\n"
        "    'mathtext_default': mpl.rcParams['mathtext.default'],\n"
        "    'cycle0': list(cyc[0]),\n"
        "}))\n"
    )
    out = subprocess.check_output([sys.executable, "-c", code], text=True)
    return json.loads(out.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def default_rc():
    # Arrange
    # Act
    rc = _run(None)
    # Assert
    return rc


@pytest.fixture(scope="module")
def scitex_rc():
    # Arrange
    # Act
    rc = _run("scitex.plt")
    # Assert
    return rc


def test_default_brand_keeps_matplotlib_font_size(default_rc):
    # Arrange
    expected = 10.0  # matplotlib default, not SCITEX 7
    # Act
    actual = default_rc["font_size"]
    # Assert
    assert actual == expected


def test_default_brand_keeps_top_spine_visible(default_rc):
    # Arrange
    # Act
    actual = default_rc["spines_top"]
    # Assert
    assert actual is True


def test_scitex_brand_sets_font_size(scitex_rc):
    # Arrange
    # Act
    actual = scitex_rc["font_size"]
    # Assert
    assert actual == 7.0


def test_scitex_brand_sets_titlesize(scitex_rc):
    # Arrange
    # Act
    actual = scitex_rc["titlesize"]
    # Assert
    assert actual == 8.0


def test_scitex_brand_sets_labelsize(scitex_rc):
    # Arrange
    # Act
    actual = scitex_rc["labelsize"]
    # Assert
    assert actual == 7.0


def test_scitex_brand_hides_top_spine(scitex_rc):
    # Arrange
    # Act
    actual = scitex_rc["spines_top"]
    # Assert
    assert actual is False


def test_scitex_brand_sets_mathtext_default(scitex_rc):
    # Arrange
    # Act
    actual = scitex_rc["mathtext_default"]
    # Assert
    assert actual == "regular"


def test_scitex_brand_sets_house_color_cycle(scitex_rc):
    # Arrange
    expected = (0.0, 0.5, 0.75)  # SCITEX house "blue" from figrecipe palette
    # Act
    r, g, b = scitex_rc["cycle0"][:3]
    actual = (round(r, 3), round(g, 3), round(b, 3))
    # Assert
    assert actual == expected


def test_apply_brand_style_returns_false_for_default_brand():
    # Arrange
    import figrecipe._brand_style as bs

    bs._APPLIED = False
    # Act
    result = apply_brand_style("figrecipe")
    # Assert
    assert result is False


def test_apply_brand_style_returns_false_for_unknown_brand():
    # Arrange
    import figrecipe._brand_style as bs

    bs._APPLIED = False
    # Act
    result = apply_brand_style("some.other.brand")
    # Assert
    assert result is False


def test_apply_brand_style_is_idempotent():
    # Arrange
    import figrecipe._brand_style as bs

    bs._APPLIED = False
    apply_brand_style("scitex.plt")
    # Act
    second = apply_brand_style("scitex.plt")
    bs._APPLIED = False  # restore shared state
    # Assert
    assert second is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
