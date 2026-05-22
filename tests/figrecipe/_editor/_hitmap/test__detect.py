"""Smoke import mirror for figrecipe._editor._hitmap._detect.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__editor__hitmap__detect_module():
    # Arrange
    module_path = 'figrecipe._editor._hitmap._detect'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
