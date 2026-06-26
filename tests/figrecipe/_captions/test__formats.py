"""Smoke import mirror for figrecipe._captions._formats.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import__captions__formats_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._captions._formats"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_caption_only_tex_has_no_figure_environment():
    # Arrange
    from figrecipe._captions._formats import format_caption_only_tex

    # Act
    out = format_caption_only_tex("Two conditions (n=3).", label_slug="fig01")
    # Assert: writer-compatible fragment must NOT open a figure float.
    assert "\\begin{figure}" not in out


def test_caption_only_tex_emits_caption_and_label():
    # Arrange
    from figrecipe._captions._formats import format_caption_only_tex

    # Act
    out = format_caption_only_tex("Latency comparison.", label_slug="fig01")
    # Assert
    assert out == "\\caption{Latency comparison.}\n\\label{fig:fig01}\n"


def test_caption_only_tex_escapes_latex_specials():
    # Arrange
    from figrecipe._captions._formats import format_caption_only_tex

    # Act: an unescaped % would comment out the rest of the LaTeX line.
    out = format_caption_only_tex("Throughput up 5% & stable_runs.", label_slug="f")
    # Assert
    assert "5\\% \\& stable\\_runs" in out


def test_caption_only_tex_omits_label_when_slug_none():
    # Arrange
    from figrecipe._captions._formats import format_caption_only_tex

    # Act: no slug -> no \label, so the consumer auto-labels by filename stem.
    out = format_caption_only_tex("Some caption.", label_slug=None)
    # Assert: caption present and NO label line at all.
    assert out == "\\caption{Some caption.}\n"
