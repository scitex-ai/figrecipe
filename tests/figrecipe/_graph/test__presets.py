"""Smoke import mirror for figrecipe._graph._presets.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import__graph__presets_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe._graph._presets"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_unregister_builtin_preset_points_to_override():
    # Arrange
    from figrecipe._graph._presets import unregister_preset

    # Act
    # Assert: refusing a built-in names it and points at the override path.
    with pytest.raises(
        ValueError,
        match=r"Cannot unregister built-in preset 'default'.*override=True",
    ):
        unregister_preset("default")


def test_unregister_missing_preset_lists_removable_presets():
    # Arrange
    from figrecipe._graph._presets import register_preset, unregister_preset

    register_preset("my_temp_preset", {})
    # Act
    # Assert: the not-found message lists the removable user presets.
    try:
        with pytest.raises(
            ValueError,
            match=r"Preset 'no_such_preset' does not exist.*my_temp_preset",
        ):
            unregister_preset("no_such_preset")
    finally:
        unregister_preset("my_temp_preset")


def test_unregister_missing_preset_with_no_user_presets_reads_gracefully():
    # Arrange
    from figrecipe._graph import _presets

    # Snapshot/clear the module-global user presets so this exercises the
    # empty-registry branch regardless of what other tests registered.
    saved = dict(_presets._user_presets)
    _presets._user_presets.clear()
    # Act
    # Assert: with no user presets, the not-found message says so.
    try:
        with pytest.raises(
            ValueError,
            match=r"Preset 'no_such_preset' does not exist.*No user presets are registered",
        ):
            _presets.unregister_preset("no_such_preset")
    finally:
        _presets._user_presets.update(saved)
