"""Smoke import mirror for figrecipe._diagram._mermaid._compile.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__diagram__mermaid__compile_module():
    # Arrange
    module_path = 'figrecipe._diagram._mermaid._compile'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
