"""Typed CSV round-trip for the dtypes the plain str() writer cannot carry.

src<->tests mirror for figrecipe._utils._numpy_io (card figrecipe-csv-roundtrip-
writer-reader-asymmetry, Slice 2).

bool, timedelta64, and MaskedArray each failed the plain save_array_csv (str) +
load_array_csv (np.array(..., dtype)) pair in a different way:

  bool        -> written "True"/"False", read as np.array([...],dtype=bool) =
                 ALL TRUE (numpy treats any non-empty string as True) -- silent.
  timedelta   -> written "0 seconds"/"3600 seconds", read with
                 dtype=timedelta64[s] -> CRASH.
  MaskedArray -> mask recorded nowhere; data cells "1.0/--/3.0" -> crash / loss.

The fix makes the writer and reader one typed pair via a ``# fmt: 2`` header
(opt-in): bool as 0/1, timedelta as integer counts + unit suffix, masked arrays
as data columns + trailing mask columns. Every OTHER dtype keeps the exact plain
(unmarked) output, so existing files/recipes are byte-identical and the legacy
reader path is untouched. These tests pin the round-trip at the DATA level
(array in == array out, dtype included) -- the card's required instrument, not a
pixel MSE comparison.
"""

import numpy as np
import pytest


def _roundtrip(arr, dtype=None):
    # Arrange: a real temp CSV via the public save.
    import tempfile
    from pathlib import Path

    from figrecipe._utils._numpy_io import load_array_csv, save_array_csv

    d = Path(tempfile.mkdtemp())
    p = d / "rt.csv"
    # Act
    save_array_csv(arr, p)
    return load_array_csv(p, dtype=np.dtype(dtype) if dtype else None)


def test_import__utils__numpy_io_module():
    # Arrange
    module_path = "figrecipe._utils._numpy_io"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_bool_1d_round_trips_values_and_dtype():
    # Arrange
    arr = np.array([True, False, True, False])
    # Act
    out = _roundtrip(arr, "bool")
    # Assert: dtype is bool AND the values are preserved (not all-true).
    assert out.dtype == np.dtype("bool") and out.tolist() == [True, False, True, False]


def test_bool_2d_round_trips_values_and_dtype():
    # Arrange
    arr = np.array([[True, False], [False, True]])
    # Act
    out = _roundtrip(arr, "bool")
    # Assert
    assert out.dtype == np.dtype("bool") and out.tolist() == [[True, False], [False, True]]


def test_timedelta_seconds_round_trips():
    # Arrange: the card's failure -- "0 seconds"/"3600 seconds" crashed the load.
    arr = np.array([0, 3600, 7200], dtype="timedelta64[s]")
    # Act
    out = _roundtrip(arr, "timedelta64[s]")
    # Assert: dtype + exact integer counts in the array's own unit.
    assert out.dtype == np.dtype("timedelta64[s]") and out.astype("int64").tolist() == [0, 3600, 7200]


def test_timedelta_milliseconds_round_trips():
    # Arrange: a different unit (ms) with a negative value.
    arr = np.array([5, -10, 15], dtype="timedelta64[ms]")
    # Act
    out = _roundtrip(arr, "timedelta64[ms]")
    # Assert: dtype + counts survive the round-trip.
    assert out.dtype == np.dtype("timedelta64[ms]") and out.astype("int64").tolist() == [5, -10, 15]


def test_masked_1d_preserves_data_and_mask():
    # Arrange: the card's failure -- the mask was recorded nowhere.
    m = np.ma.array([1.0, 2.0, 3.0], mask=[False, True, False])
    # Act
    out = _roundtrip(m, "float64")
    # Assert: it is a masked array whose DATA and MASK both round-trip.
    assert (
        isinstance(out, np.ma.MaskedArray)
        and out.data.tolist() == [1.0, 2.0, 3.0]
        and out.mask.tolist() == [False, True, False]
    )


def test_masked_2d_preserves_data_and_mask():
    # Arrange
    m = np.ma.array([[1.0, 2.0], [3.0, 4.0]], mask=[[False, True], [False, False]])
    # Act
    out = _roundtrip(m, "float64")
    # Assert
    assert (
        isinstance(out, np.ma.MaskedArray)
        and out.data.tolist() == [[1.0, 2.0], [3.0, 4.0]]
        and out.mask.tolist() == [[False, True], [False, False]]
    )


def test_float_array_keeps_plain_unmarked_output(tmp_path):
    """The plain path is byte-identical: a float array must NOT gain a ``# fmt``
    marker, so existing files/recipes are unchanged on disk."""
    # Arrange
    from figrecipe._utils._numpy_io import save_array_csv

    p = tmp_path / "plain.csv"
    # Act
    save_array_csv(np.array([1.5, 2.5, 3.5]), p)
    # Assert: exactly the historical plain output -- no marker line.
    assert p.read_text().strip() == "1.5\n2.5\n3.5"


def test_float_array_round_trips_plain(tmp_path):
    # Arrange
    from figrecipe._utils._numpy_io import load_array_csv, save_array_csv

    p = tmp_path / "plain.csv"
    save_array_csv(np.array([1.5, 2.5, 3.5]), p)
    # Act
    out = load_array_csv(p, dtype=np.dtype("float64"))
    # Assert: a normal float still round-trips through the (unchanged) plain path.
    assert out.tolist() == [1.5, 2.5, 3.5]


def test_legacy_unmarked_bool_csv_still_loads(tmp_path):
    """Back-compat: an OLD (no-marker) bool CSV written by the historical
    writer must still LOAD through the legacy path -- we only change the writer
    for new files, never the reader's handling of old ones."""
    # Arrange
    from figrecipe._utils._numpy_io import load_array_csv

    p = tmp_path / "legacy.csv"
    p.write_text("True\nFalse\nTrue\n")
    # Act
    out = load_array_csv(p, dtype=np.dtype("bool"))
    # Assert: it loads (dtype + shape preserved); the legacy value semantics are
    # intentionally unchanged (this is the pre-v2 behaviour).
    assert out.dtype == np.dtype("bool") and len(out) == 3


def test_legacy_unmarked_float_csv_still_loads(tmp_path):
    # Arrange
    from figrecipe._utils._numpy_io import load_array_csv

    p = tmp_path / "legacy.csv"
    p.write_text("1.5\n2.5\n3.5\n")
    # Act
    out = load_array_csv(p, dtype=np.dtype("float64"))
    # Assert: legacy plain float load is untouched.
    assert out.tolist() == [1.5, 2.5, 3.5]
