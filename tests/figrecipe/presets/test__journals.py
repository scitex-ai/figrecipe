"""Smoke import mirror for figrecipe.presets._journals.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import_presets__journals_module():
    # Arrange
    module_path = 'figrecipe.presets._journals'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
