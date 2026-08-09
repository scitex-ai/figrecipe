"""Tests for STX-FM012 raster-tiling-of-rendered-panels AST rule.

Real ast.parse + RasterTilingChecker — no mocks. Each test follows
Arrange / Act / Assert with one assertion and a >=3-word behavioural name.

The rule is deliberately narrow, so most of these tests are NEGATIVE: the
cost of a false positive is an author fighting the linter over ordinary
image work.
"""

from __future__ import annotations

import ast

import pytest

# Skip the whole module gracefully if scitex_dev isn't importable in this
# environment — the checker itself is import-guarded the same way.
pytest.importorskip("scitex_dev.linter.checker")

from figrecipe._quality._linter_plugin import get_plugin  # noqa: E402
from figrecipe._quality._raster_tiling_checker import (  # noqa: E402
    RasterTilingChecker,
)

_PLUGIN = get_plugin()
_FM012 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM012")
_FM013 = next(r for r in _PLUGIN["rules"] if r.id == "STX-FM013")


def _make_config():
    """Real linter config; no mocks."""
    from scitex_dev.linter.config import load_config

    return load_config(start_path=__file__)


def _run(src: str):
    """Parse *src* and run RasterTilingChecker; return collected issues."""
    tree = ast.parse(src)
    checker = RasterTilingChecker(
        src.splitlines(), _make_config(), rule=_FM012, rescale_rule=_FM013
    )
    checker.visit(tree)
    return checker.issues


def _fired(issues):
    return any(i.rule.id == "STX-FM012" for i in issues)


def _rescale_fired(issues):
    return any(i.rule.id == "STX-FM013" for i in issues)


# ---------------------------------------------------------------------------
# POSITIVE — fires on compositing rendered panels
# ---------------------------------------------------------------------------


def test_warns_on_pil_paste_of_rendered_panels():
    # Arrange: the shape that actually shipped a broken composite.
    src = (
        "from PIL import Image\n"
        "canvas = Image.new('RGB', (2000, 1000))\n"
        "panel = Image.open('figures/fig02_a.png')\n"
        "canvas.paste(panel, (0, 0))\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_warns_on_cv2_hconcat_of_panels():
    # Arrange
    src = "import cv2\nrow = cv2.hconcat([left, right])\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_warns_on_alpha_composite():
    # Arrange
    src = "from PIL import Image\nout = base.alpha_composite(overlay)\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


def test_flags_the_compositing_line_not_the_import():
    # Arrange
    src = "from PIL import Image\ncanvas.paste(panel, (0, 0))\n"
    # Act
    issues = _run(src)
    # Assert
    assert issues[0].line == 2


def test_warns_when_the_imaging_import_comes_after_the_call():
    # Arrange: candidates are emitted at module finalize, so import order
    # must not decide whether the rule fires.
    src = "canvas.paste(panel, (0, 0))\nimport cv2\n"
    # Act
    issues = _run(src)
    # Assert
    assert _fired(issues)


# ---------------------------------------------------------------------------
# NEGATIVE — the false positives this rule must not produce
# ---------------------------------------------------------------------------


def test_does_not_warn_without_an_imaging_import():
    # Arrange: `paste` on some unrelated object is not raster compositing.
    src = "clipboard.paste(text)\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


def test_does_not_warn_on_opening_an_image_for_analysis():
    # Arrange: loading image DATA is ordinary work, not tiling.
    src = "from PIL import Image\nimg = Image.open('data/sample.tif')\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


def test_does_not_warn_fm012_on_a_bare_resize():
    # Arrange: a resize is not compositing, so FM012 must stay silent.
    src = "from PIL import Image\nsmall = img.resize((256, 256))\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# FM013 rendered-panel rescale. The GATE is the whole rule: a resize only means
# panel rescale if this module composites panels at all. Otherwise it is
# someone scaling an array in order to plot it, which must stay silent.
# ---------------------------------------------------------------------------


def test_fm013_warns_on_resize_in_a_compositing_module():
    # Arrange: resize + paste together is panel rescale.
    src = (
        "from PIL import Image\n"
        "panel = Image.open('figures/fig02_a.png')\n"
        "panel = panel.resize((800, 600))\n"
        "canvas.paste(panel, (0, 0))\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert _rescale_fired(issues)


def test_fm013_warns_on_thumbnail_in_a_compositing_module():
    # Arrange
    src = (
        "from PIL import Image\n"
        "panel.thumbnail((400, 300))\n"
        "canvas.paste(panel, (0, 0))\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert _rescale_fired(issues)


def test_fm013_stays_silent_on_a_resize_with_no_compositing():
    # Arrange: the load-bearing negative. Scaling an array to plot it is
    # ordinary analysis and must not be flagged as panel rescale.
    src = "from PIL import Image\nsmall = Image.open('data/s.tif').resize((256, 256))\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _rescale_fired(issues)


def test_fm013_stays_silent_without_an_imaging_import():
    # Arrange: `resize` on some unrelated object, alongside a paste.
    src = "widget.resize(800, 600)\ncanvas.paste(x, (0, 0))\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _rescale_fired(issues)


def test_fm013_flags_the_resize_line_not_the_paste_line():
    # Arrange
    src = (
        "from PIL import Image\n"
        "panel = panel.resize((800, 600))\n"
        "canvas.paste(panel, (0, 0))\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert [i.line for i in issues if i.rule.id == "STX-FM013"] == [2]


def test_fm013_honours_its_own_opt_out_comment():
    # Arrange
    src = (
        "from PIL import Image\n"
        "panel = panel.resize((800, 600))  # stx-allow: STX-FM013\n"
        "canvas.paste(panel, (0, 0))\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert not _rescale_fired(issues)


def test_fm013_is_registered_in_the_plugin():
    # Arrange
    plugin = get_plugin()
    # Act
    ids = [r.id for r in plugin["rules"]]
    # Assert
    assert "STX-FM013" in ids


def test_fm013_defaults_to_warning_so_the_category_floor_promotes_it():
    # Arrange
    expected = "warning"
    # Act
    actual = _FM013.severity
    # Assert
    assert actual == expected


def test_does_not_warn_on_fromarray_for_plotting():
    # Arrange
    src = "from PIL import Image\nim = Image.fromarray(arr)\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


def test_does_not_warn_on_a_figrecipe_compose_script():
    # Arrange: the canonical path must stay silent.
    src = "import figrecipe as fr\nfr.compose(['a.yaml', 'b.yaml'], ncols=2)\n"
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# Escape hatch — the documented way out for genuine image-DATA montages
# ---------------------------------------------------------------------------


def test_does_not_warn_when_opt_out_comment_present():
    # Arrange
    src = (
        "from PIL import Image\n"
        "canvas.paste(tile, (0, 0))  # stx-allow: STX-FM012\n"
    )
    # Act
    issues = _run(src)
    # Assert
    assert not _fired(issues)


# ---------------------------------------------------------------------------
# Registration — the rule must actually reach the runner
# ---------------------------------------------------------------------------


def test_rule_is_registered_in_the_plugin():
    # Arrange
    plugin = get_plugin()
    # Act
    ids = [r.id for r in plugin["rules"]]
    # Assert
    assert "STX-FM012" in ids


def test_rule_emits_under_the_figure_category():
    # Arrange
    expected = "figure"
    # Act
    actual = _FM012.category
    # Assert
    assert actual == expected


def test_rule_defaults_to_warning_so_the_category_floor_promotes_it():
    # Arrange: scitex-dev promotes category=figure warnings to ERROR under
    # project-type:research. A hardcoded error here would override that floor.
    expected = "warning"
    # Act
    actual = _FM012.severity
    # Assert
    assert actual == expected
