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


# ── _process_single_arg: date lists are DATA, not text ───────────────────────
#
# A one-point date series ``[np.datetime64("2026-08-08")]`` was recorded as the
# TEXT "[np.datetime64('2026-08-08')]" because only numeric dtype kinds took
# the array path; replay could not convert it to axis units and a correct
# figure failed validation (2026-09-04). Real helpers, no patching.


def _process(value):
    import datetime as _dt  # noqa: F401  (documents what the lists hold)

    from figrecipe._recorder._utils import _process_single_arg
    from figrecipe._utils._numpy_io import should_store_inline, to_serializable

    return _process_single_arg(
        "x", value, should_store_inline, to_serializable, _is_native
    )


def test_datetime64_list_is_recorded_with_a_datetime_dtype():
    # Arrange
    value = [np.datetime64("2026-08-08")]
    # Act
    out = _process(value)
    # Assert
    assert str(out.get("dtype", "")).startswith("datetime64")


def test_datetime64_list_is_not_recorded_as_repr_text():
    # Arrange
    value = [np.datetime64("2026-08-08")]
    # Act
    out = _process(value)
    # Assert
    assert "np.datetime64" not in str(out.get("data"))


def test_python_date_list_is_recorded_with_a_datetime_dtype():
    # Arrange
    import datetime as _dt

    value = [_dt.date(2026, 8, 8), _dt.date(2026, 8, 9)]
    # Act
    out = _process(value)
    # Assert
    assert str(out.get("dtype", "")).startswith("datetime64")


def test_control_numeric_list_still_takes_the_array_path():
    # Arrange
    value = [1, 2, 3]
    # Act
    out = _process(value)
    # Assert
    assert str(out.get("dtype", "")).startswith("int")


def test_control_string_list_does_not_get_a_datetime_dtype():
    """Control: a list of labels is not data and must not be coerced."""
    # Arrange
    value = ["a", "b"]
    # Act
    out = _process(value)
    # Assert
    assert not str(out.get("dtype", "")).startswith("datetime64")
