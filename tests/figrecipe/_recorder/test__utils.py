"""Tests for figrecipe._recorder._utils.

Covers the numpy-scalar coercion in ``_process_scalar`` (regression for a
NeuroVista Fig 2 bug: ``np.int64`` positions were serialized as the string
``'0'`` and broke replay on a category-unit axis).
"""

import numpy as np
import pytest

from figrecipe._recorder._utils import _process_scalar


def _is_native(value):
    """Mimic the recorder's serializability check: native JSON/YAML scalars only.

    ``np.generic`` instances are deliberately NOT native here -- without
    coercion they fall through to ``str(value)`` in ``_process_scalar``.
    """
    return isinstance(value, (bool, int, float, str)) and not isinstance(
        value, np.generic
    )


def test_import__recorder__utils_module():
    # Arrange
    module_path = "figrecipe._recorder._utils"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


class TestProcessScalarNumpyCoercion:
    """``_process_scalar`` must coerce numpy scalars to native Python numbers."""

    def test_numpy_int_serialized_value_equals_zero(self):
        # Arrange
        value = np.int64(0)
        # Act
        out = _process_scalar("x", value, _is_native)
        # Assert
        assert out["data"] == 0

    def test_numpy_int_serialized_as_python_int(self):
        # Arrange
        value = np.int64(0)
        # Act
        out = _process_scalar("x", value, _is_native)
        # Assert
        assert isinstance(out["data"], int)

    def test_numpy_int_not_serialized_as_string(self):
        # Arrange
        value = np.int64(0)
        # Act
        out = _process_scalar("x", value, _is_native)
        # Assert
        assert not isinstance(out["data"], str)

    def test_numpy_float_serialized_as_python_float(self):
        # Arrange
        value = np.float64(0.93)
        # Act
        out = _process_scalar("y", value, _is_native)
        # Assert
        assert isinstance(out["data"], float)

    def test_numpy_bool_serialized_as_python_bool(self):
        # Arrange
        value = np.bool_(True)
        # Act
        out = _process_scalar("flag", value, _is_native)
        # Assert
        assert out["data"] is True

    def test_native_string_passes_through_unchanged(self):
        # Arrange
        value = "label"
        # Act
        out = _process_scalar("s", value, _is_native)
        # Assert
        assert out["data"] == "label"
