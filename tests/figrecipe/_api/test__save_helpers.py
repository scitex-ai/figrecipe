"""Smoke import mirror for figrecipe._api._save_helpers.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import__api__save_helpers_module():
    # Arrange
    module_path = "figrecipe._api._save_helpers"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


from figrecipe._api._save_helpers import format_saved_pair, log_save_result


class _FakeLogger:
    """Hand-rolled logger that records (level, message) calls (no mocks)."""

    def __init__(self):
        self.calls = []

    def success(self, msg):
        self.calls.append(("success", msg))

    def error(self, msg):
        self.calls.append(("error", msg))

    def info(self, msg):
        self.calls.append(("info", msg))

    def warning(self, msg):
        self.calls.append(("warning", msg))


class _FakeResult:
    def __init__(self, valid, summary_text="SUMMARY-BODY"):
        self.valid = valid
        self._summary_text = summary_text

    def summary(self):
        return self._summary_text


class TestFormatSavedPair:
    def test_same_stem_uses_compact_brace_form(self):
        # Arrange
        # Act
        out = format_saved_pair("/a/b/fig.png", "/a/b/fig.yaml")
        # Assert
        assert out == "/a/b/fig.{png,yaml}"

    def test_different_stem_falls_back_to_plus_form(self):
        # Arrange
        # Act
        out = format_saved_pair("/a/b/fig.png", "/a/b/other.yaml")
        # Assert
        assert out == "/a/b/fig.png + /a/b/other.yaml"


class TestLogSaveResult:
    def test_failed_validation_emits_error_with_summary(self):
        # Arrange
        lg = _FakeLogger()
        result = _FakeResult(valid=False, summary_text="WHY: MSE exceeds")
        # Act
        log_save_result("/a/fig.png", "/a/fig.yaml", result, _logger=lg)
        # Assert
        assert any(
            lvl == "error" and "WHY: MSE exceeds" in msg for lvl, msg in lg.calls
        )

    def test_passed_validation_emits_no_error(self):
        # Arrange
        lg = _FakeLogger()
        # Act
        log_save_result(
            "/a/fig.png", "/a/fig.yaml", _FakeResult(valid=True), _logger=lg
        )
        # Assert
        assert all(lvl != "error" for lvl, _ in lg.calls)

    def test_plain_save_emits_success(self):
        # Arrange
        lg = _FakeLogger()
        # Act
        log_save_result("/a/fig.png", "/a/fig.yaml", None, _logger=lg)
        # Assert
        assert any(lvl == "success" for lvl, _ in lg.calls)

    def test_verbose_false_emits_nothing(self):
        # Arrange
        lg = _FakeLogger()
        # Act
        log_save_result("/a/fig.png", "/a/fig.yaml", None, verbose=False, _logger=lg)
        # Assert
        assert lg.calls == []
