"""Smoke import mirror for figrecipe.styles._finalize.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import_styles__finalize_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe.styles._finalize"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# ── pie labels: the path the operator reported (2026-09-02) ───────────────────
#
# finalize_special_plots() sets each pie text's family. It must be a LIST so
# matplotlib falls back per glyph for CJK labels; a bare string was the tofu.


def _pie_with_japanese_labels():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.pie([3, 2, 1], labels=["売上", "経費", "利益"], autopct="%1.0f%%")
    return fig, ax


def test_pie_text_family_is_a_list_after_finalize():
    # Arrange
    import matplotlib.pyplot as plt

    from figrecipe.styles._finalize import finalize_special_plots

    fig, ax = _pie_with_japanese_labels()
    # Act
    finalize_special_plots(ax, {"font_family": "DejaVu Sans"})
    families = [t.get_fontfamily() for t in ax.texts if t.get_text()]
    plt.close(fig)
    # Assert
    assert all(isinstance(f, list) for f in families)


def test_pie_text_family_starts_with_the_requested_font_after_finalize():
    # Arrange
    import matplotlib.pyplot as plt

    from figrecipe.styles._finalize import finalize_special_plots

    fig, ax = _pie_with_japanese_labels()
    # Act
    finalize_special_plots(ax, {"font_family": "DejaVu Sans"})
    firsts = {t.get_fontfamily()[0] for t in ax.texts if t.get_text()}
    plt.close(fig)
    # Assert
    assert firsts == {"DejaVu Sans"}
