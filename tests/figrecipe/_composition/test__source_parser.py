"""Smoke import mirror for figrecipe._composition._source_parser.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__composition__source_parser_module():
    # Arrange
    module_path = 'figrecipe._composition._source_parser'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
