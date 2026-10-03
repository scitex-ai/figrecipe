"""Smoke import mirror for figrecipe._api._extract.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__api__extract_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._api._extract'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def _record(*calls):
    from figrecipe._recorder._core import AxesRecord, FigureRecord

    return FigureRecord(axes={"ax_0_0": AxesRecord(position=(0, 0), calls=list(calls))})


def _call(call_id, function, args, **kwargs):
    from figrecipe._recorder._core import CallRecord

    return CallRecord(
        id=call_id,
        function=function,
        args=[{"name": f"arg{i}", "data": value} for i, value in enumerate(args)],
        kwargs=kwargs,
    )


def test_record_extract_keeps_function_specific_fields():
    # Arrange
    from figrecipe._api._extract import extract_record_data, to_json_serializable

    record = _record(
        _call("bar", "bar", [[1, 2], [3, 4]]),
        _call("hist", "hist", [[1, 2, 3]], bins=[0, 2, 4], weights=[1, 1, 2]),
        _call("scatter", "scatter", [[1, 2], [3, 4]], c=[0.2, 0.8], s=[10, 20]),
        _call("errors", "errorbar", [[1, 2], [3, 4]], yerr=[0.1, 0.2]),
        _call("label", "set_title", [[1, 2]]),
    )
    expected = {
        "bar": {"x": [1, 2], "height": [3, 4]},
        "hist": {"x": [1, 2, 3], "weights": [1, 1, 2], "bins": [0, 2, 4]},
        "scatter": {"x": [1, 2], "y": [3, 4], "c": [0.2, 0.8], "s": [10, 20]},
        "errors": {"x": [1, 2], "y": [3, 4], "yerr": [0.1, 0.2]},
    }
    # Act
    observed = to_json_serializable(extract_record_data(record))
    # Assert
    assert observed == expected


def test_public_saved_recipe_extract_delegates_the_same_record_data():
    # Arrange
    from pathlib import Path

    import figrecipe as fr
    from figrecipe._api._extract import extract_record_data, to_json_serializable
    from figrecipe._serializer import load_recipe

    gallery = Path(fr.__file__).resolve().parent / "_django" / "gallery_templates"
    recipe = gallery / "plot_plot.yaml"
    expected = {
        cid: {
            key: [
                float(value)
                for value in (
                    gallery / "plot_plot_data" / f"{cid}_{key}.csv"
                ).read_text().splitlines()
            ]
            for key in ("x", "y")
        }
        for cid in ("sin", "cos")
    }
    # Act
    observed = {
        "public": to_json_serializable(fr.extract_data(recipe)),
        "record": to_json_serializable(extract_record_data(load_recipe(recipe))),
    }
    # Assert
    assert observed == {"public": expected, "record": expected}


def test_live_inline_unsaved_call_is_read_without_reloading_disk(tmp_path):
    # Arrange
    import matplotlib.pyplot as plt

    import figrecipe as fr
    from figrecipe._api._extract import (
        csv_bytes_from_record,
        extract_record_data,
        table_from_record,
        to_json_serializable,
    )
    from figrecipe._serializer import save_recipe

    # Nonempty numeric arrays are file-backed (INLINE_THRESHOLD=0). Genuine
    # categorical lists stay inline, so this positive CSV contract does not
    # silently repair or claim coverage of the separate live-sentinel defect.
    fig, ax = fr.subplots()
    try:
        ax.plot(["A", "B"], ["C", "D"], id="saved")
        recipe = tmp_path / "before.yaml"
        save_recipe(fig.record, recipe)
        disk_before = recipe.read_bytes()
        ax.plot(["E", "F"], ["G", "H"], id="unsaved")
        expected = {
            "saved": {"x": ["A", "B"], "y": ["C", "D"]},
            "unsaved": {"x": ["E", "F"], "y": ["G", "H"]},
        }
        # Act
        observed = {
            "record": to_json_serializable(extract_record_data(fig.record)),
            "disk": to_json_serializable(fr.extract_data(recipe)),
            "csv": csv_bytes_from_record(fig.record),
            "table": table_from_record(fig.record),
            "disk_unchanged": recipe.read_bytes() == disk_before,
        }
    finally:
        plt.close(fig._fig)
    # Assert
    assert observed == {
        "record": expected,
        "disk": {"saved": expected["saved"]},
        "csv": b"saved_x,saved_y,unsaved_x,unsaved_y\r\nA,C,E,G\r\nB,D,F,H\r\n",
        "table": (
            ["saved_x", "saved_y", "unsaved_x", "unsaved_y"],
            [["A", "C", "E", "G"], ["B", "D", "F", "H"]],
        ),
        "disk_unchanged": True,
    }


def test_record_csv_keeps_quoted_columns_native_order_and_padding():
    # Arrange
    from figrecipe._api._extract import csv_bytes_from_record

    record = _record(
        _call("a,b", "bar", [[1, 2], [3, 4]]),
        _call("hist", "hist", [[4, 5, 6]]),
        _call("label", "set_title", [[8, 9]]),
    )
    expected = (
        b'"a,b_x","a,b_y",hist_x,hist_y\r\n'
        b"1,3,0,4\r\n2,4,1,5\r\n,,2,6\r\n"
    )
    # Act
    observed = csv_bytes_from_record(record)
    # Assert
    assert observed == expected


def test_record_table_reads_live_arrays_with_missing_call_cells():
    # Arrange
    import matplotlib.pyplot as plt
    import numpy as np

    import figrecipe as fr
    from figrecipe._api._extract import table_columns, table_from_record

    fig, ax = fr.subplots()
    try:
        ax.plot(np.arange(20), np.arange(20) + 10, id="large")
        ax.plot([2, 3], [4, 5], id="short")
        # Act
        names, rows = table_from_record(fig.record)
        observed = {"columns": table_columns(names, rows), "rows": rows}
    finally:
        plt.close(fig._fig)
    # Assert
    assert observed == {
        "columns": [
            {"name": name, "dtype": "numeric"}
            for name in ("large_x", "large_y", "short_x", "short_y")
        ],
        "rows": [[0, 10, 2, 4], [1, 11, 3, 5]]
        + [[i, i + 10, None, None] for i in range(2, 20)],
    }


def test_json_conversion_preserves_nested_values_and_input_array():
    # Arrange
    import numpy as np

    from figrecipe._api._extract import to_json_serializable

    array = np.array([1, 2])
    payload = {
        "array": array,
        "nested": (np.int64(3), {"value": np.float64(4.5)}),
    }
    # Act
    observed = {
        "converted": to_json_serializable(payload),
        "array_after": array.tolist(),
    }
    # Assert
    assert observed == {
        "converted": {"array": [1, 2], "nested": [3, {"value": 4.5}]},
        "array_after": [1, 2],
    }
