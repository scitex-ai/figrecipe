"""Direct helper calls preserve explicit preferences without a Click context."""

import pytest

from figrecipe._cli._json_output import json_requested


@pytest.mark.parametrize("requested", [False, True])
def test_direct_json_preference(requested):
    # Arrange
    preference = requested
    # Act
    actual = json_requested(preference)
    # Assert
    assert actual is preference
