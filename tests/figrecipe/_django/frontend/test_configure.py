"""Smoke import mirror for figrecipe._django.frontend.configure.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__django_frontend_configure_module():
    # Arrange
    module_path = 'figrecipe._django.frontend.configure'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
