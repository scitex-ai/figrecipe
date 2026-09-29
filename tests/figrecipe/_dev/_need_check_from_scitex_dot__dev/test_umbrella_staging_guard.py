"""Guard placeholder for umbrella-staging smoke tests.

When ``scitex_dev.plt`` is unavailable, the plt-gated modules in this
directory are collection-ignored (see conftest.py). Without this file,
``pytest`` on the directory would exit 5 ("no tests ran"); this single
skipped test turns that into a clean skip with exit 0. When
``scitex_dev.plt`` is present, this passes alongside the real smoke
tests.
"""

import importlib.util


def test_umbrella_staging_guard():
    # Arrange
    import pytest
    import importlib.util

    # Act
    missing = importlib.util.find_spec("scitex_dev.plt") is None

    # Assert
    if missing:
        pytest.skip(
            "umbrella-staging: scitex_dev.plt not available "
            "in installed scitex-dev"
        )
    assert True
