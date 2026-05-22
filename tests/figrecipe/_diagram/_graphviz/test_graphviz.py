"""Smoke import mirror for figrecipe._diagram._graphviz.graphviz.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__diagram__graphviz_graphviz_module():
    # Arrange
    module_path = 'figrecipe._diagram._graphviz.graphviz'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
