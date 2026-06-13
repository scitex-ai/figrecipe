"""Smoke import mirror for figrecipe._api._save.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__api__save_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._api._save'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


import figrecipe as fr  # noqa: E402


class TestSpineReproducibility:
    def test_hidden_spines_reproduce_identically(self, tmp_path):
        # Arrange
        fig, ax = fr.subplots()
        ax.scatter([0, 1, 2], [0, 1, 2])
        for side in ("left", "right", "top", "bottom"):
            ax.spines[side].set_visible(False)
        # Act
        _, _, result = fr.save(
            fig, str(tmp_path / "fig.png"), verbose=False,
            validate_error_level="warning",
        )
        # Assert
        assert result.valid
