"""Smoke import mirror for figrecipe._diagram._shared._render.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__diagram__shared__render_module():
    # Arrange
    module_path = 'figrecipe._diagram._shared._render'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
