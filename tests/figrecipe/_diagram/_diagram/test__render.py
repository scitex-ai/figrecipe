"""Smoke import mirror for figrecipe._diagram._diagram._render.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import os
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from figrecipe import Diagram
from figrecipe.styles._fonts import CJK_FONT_ENV, cjk_font, reset_cjk_font_cache


def test_import__diagram__diagram__render_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._diagram._diagram._render'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


@pytest.fixture
def fallback_override():
    """Use a real bundled face for a portable per-glyph fallback control."""
    previous = os.environ.get(CJK_FONT_ENV)
    os.environ[CJK_FONT_ENV] = "DejaVu Sans"
    reset_cjk_font_cache()
    yield "DejaVu Sans"
    if previous is None:
        os.environ.pop(CJK_FONT_ENV, None)
    else:
        os.environ[CJK_FONT_ENV] = previous
    reset_cjk_font_cache()


def _labeled_diagram(japanese=False):
    title, first, second, label = (
        ("日本語", "入力", "出力", "変換") if japanese
        else ("Flow", "Input", "Output", "Convert")
    )
    diagram = Diagram(title=title, width_mm=170, height_mm=90)
    diagram.add_box("input", first, shape="box", x_mm=40, y_mm=37,
                    width_mm=35, height_mm=26, padding_mm=3)
    diagram.add_box("output", second, shape="box", x_mm=125, y_mm=37,
                    width_mm=35, height_mm=26, padding_mm=3)
    diagram.add_container("group", title="Group" if not japanese else "工程",
                          children=["input", "output"], x_mm=82.5, y_mm=44,
                          width_mm=155, height_mm=65)
    diagram.add_arrow("input", "output", label=label, label_offset_mm=(0, 6))
    return diagram


@pytest.fixture
def fallback_render(fallback_override):
    # STIXSizeOneSym really lacks these Latin glyphs; no font lookup is mocked.
    with mpl.rc_context({"font.family": ["serif"],
                         "font.serif": ["STIXSizeOneSym"],
                         "font.sans-serif": ["STIXSizeOneSym"]}):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, ax = _labeled_diagram().render()
            fig.canvas.draw()
        yield ax, caught
        plt.close(fig)


def test_standalone_text_uses_fallback_without_recording_subplots(fallback_render):
    # Arrange
    ax, _ = fallback_render
    # Act
    families = [text.get_fontfamily() for text in ax.texts if text.get_text()]
    # Assert
    assert all("DejaVu Sans" in family for family in families)


def test_standalone_fallback_draw_has_no_missing_glyphs(fallback_render):
    # Arrange
    _, caught = fallback_render
    # Act
    missing = [str(w.message) for w in caught if "missing from font" in str(w.message)]
    # Assert
    assert missing == []


def test_standalone_keeps_original_generic_family_choices(fallback_render):
    # Arrange
    ax, _ = fallback_render
    expected = {"Input": "sans-serif", "Output": "sans-serif", "Convert": "serif",
                "Flow": "serif", "Group": "serif"}
    # Act
    first = {text.get_text(): text.get_fontfamily()[0] for text in ax.texts}
    # Assert
    assert first == expected


def test_standalone_render_does_not_change_global_fonts(fallback_override):
    # Arrange
    before = {key: list(mpl.rcParams[key]) for key in
              ("font.family", "font.sans-serif", "font.serif", "font.monospace")}
    # Act
    fig, _ = _labeled_diagram().render()
    after = {key: list(mpl.rcParams[key]) for key in before}
    plt.close(fig)
    # Assert
    assert after == before


@pytest.fixture
def installed_cjk():
    reset_cjk_font_cache()
    family = cjk_font()
    if family is None:
        pytest.skip("No installed CJK family: real Japanese render is unverified here")
    return family


def test_standalone_japanese_labels_draw_with_installed_cjk_font(installed_cjk):
    # Arrange
    # The real font precondition lives in the fixture; no lookup is mocked.
    # Act
    with mpl.rc_context(mpl.rcParamsDefault), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, _ = _labeled_diagram(japanese=True).render()
        fig.canvas.draw()
    missing = [str(w.message) for w in caught if "missing from font" in str(w.message)]
    plt.close(fig)
    # Assert
    assert missing == []


def test_native_graph_nodes_edges_and_title_use_the_same_fallback(fallback_override):
    # Arrange
    from figrecipe._diagram._shared._native_render import DiagramRenderer
    from figrecipe._diagram._shared._schema import DiagramSpec, EdgeSpec, NodeSpec

    spec = DiagramSpec(title="Flow", nodes=[NodeSpec("a", "Input"), NodeSpec("b", "Output")],
                       edges=[EdgeSpec("a", "b", label="Convert")])
    # Act
    fig, ax = DiagramRenderer(spec).render()
    families = [text.get_fontfamily() for text in [ax.title, *ax.texts] if text.get_text()]
    plt.close(fig)
    # Assert
    assert all("DejaVu Sans" in family for family in families)


def test_plain_codeblock_keeps_monospace_before_fallback(fallback_override):
    # Arrange
    diagram = Diagram(width_mm=70, height_mm=45)
    diagram.add_box("code", "Code", content=["body"], shape="codeblock",
                    x_mm=35, y_mm=22, width_mm=60, height_mm=38, padding_mm=3)
    # Act
    fig, ax = diagram.render()
    family = next(text.get_fontfamily() for text in ax.texts if text.get_text() == "body")
    plt.close(fig)
    # Assert
    assert family == ["monospace", "DejaVu Sans"]


def test_original_font_config_family_value_is_preserved(fallback_override):
    # Arrange
    from figrecipe._diagram._shared._styles_native import FONT_CONFIG, resolve_font_config

    expected = FONT_CONFIG["family"]
    # Act
    family = resolve_font_config()["family"]
    # Assert
    assert family == expected
