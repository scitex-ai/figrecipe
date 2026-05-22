"""Smoke import mirror for figrecipe.styles._fonts.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import_styles__fonts_module():
    # Arrange
    module_path = 'figrecipe.styles._fonts'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
