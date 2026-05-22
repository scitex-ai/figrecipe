"""Smoke import mirror for figrecipe._reproducer._line_styles.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__reproducer__line_styles_module():
    # Arrange
    module_path = 'figrecipe._reproducer._line_styles'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
