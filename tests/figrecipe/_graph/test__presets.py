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
    module_path = 'figrecipe._graph._presets'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_unregister_builtin_preset_points_to_override():
    from figrecipe._graph._presets import unregister_preset

    with pytest.raises(ValueError) as exc_info:
        unregister_preset("default")
    message = str(exc_info.value)
    assert "Cannot unregister built-in preset 'default'" in message
    # The message points at the supported way to change a built-in.
    assert "override=True" in message


def test_unregister_missing_preset_lists_removable_presets():
    from figrecipe._graph._presets import register_preset, unregister_preset

    register_preset("my_temp_preset", {})
    try:
        with pytest.raises(ValueError) as exc_info:
            unregister_preset("no_such_preset")
        message = str(exc_info.value)
        assert "Preset 'no_such_preset' does not exist" in message
        # Only removable (user) presets are listed.
        assert "my_temp_preset" in message
    finally:
        unregister_preset("my_temp_preset")


def test_unregister_missing_preset_with_no_user_presets_reads_gracefully():
    from figrecipe._graph import _presets

    # Snapshot/clear the module-global user presets so this exercises the
    # empty-registry branch regardless of what other tests registered.
    saved = dict(_presets._user_presets)
    _presets._user_presets.clear()
    try:
        with pytest.raises(ValueError) as exc_info:
            _presets.unregister_preset("no_such_preset")
        message = str(exc_info.value)
        assert "Preset 'no_such_preset' does not exist" in message
        assert "No user presets are registered." in message
    finally:
        _presets._user_presets.update(saved)
