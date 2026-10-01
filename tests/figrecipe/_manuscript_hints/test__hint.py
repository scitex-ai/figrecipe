"""Tests for the validated hint shape.

The point of the validator is that a wrong hint fails HERE rather than
rendering blank in scitex-writer's UI, so most of these assert on the refusal.
Real objects, no mocks. One assertion per test, AAA markers.
"""

from __future__ import annotations

import pytest

from figrecipe._manuscript_hints._hint import (
    HINT_KEYS,
    KINDS,
    SEVERITIES,
    SOURCE,
    Hint,
    HintValidationError,
)


def _valid(**overrides):
    """A hint that passes validation, with fields overridable per test."""
    fields = dict(
        kind="stale-recipe",
        severity="warning",
        message="figure is newer than its recipe; re-save through figrecipe",
        claim_id="figures/fig01",
        location="figures/fig01.png",
    )
    fields.update(overrides)
    return Hint(**fields)


def _refusal_text(**overrides) -> str:
    """The validator's message for an invalid hint, or '' if it allowed it.

    Lets a test assert on the message with a SINGLE assertion — pairing
    ``pytest.raises`` with a separate text assert would be two.
    """
    try:
        _valid(**overrides)
    except HintValidationError as exc:
        return str(exc)
    return ""


def test_valid_hint_constructs():
    # Arrange
    overrides = {"kind": "stale-recipe"}
    # Act
    hint = _valid(**overrides)
    # Assert
    assert hint.kind == "stale-recipe"


def test_source_defaults_to_figrecipe():
    # Arrange
    overrides = {}
    # Act
    hint = _valid(**overrides)
    # Assert
    assert hint.source == SOURCE


def test_unknown_kind_is_rejected():
    # Arrange
    overrides = {"kind": "not-a-kind"}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_unknown_kind_refusal_names_the_valid_set():
    # Arrange
    overrides = {"kind": "not-a-kind"}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert "stale-recipe" in text


def test_unknown_severity_is_rejected():
    # Arrange
    overrides = {"severity": "catastrophic"}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_empty_message_is_rejected():
    # Arrange
    overrides = {"message": ""}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_whitespace_only_message_is_rejected():
    # Arrange
    overrides = {"message": "   "}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_non_string_claim_id_is_rejected():
    # Arrange
    overrides = {"claim_id": 17}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_non_string_message_refusal_names_the_received_type():
    # Arrange
    overrides = {"message": None}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert "NoneType" in text


def test_empty_location_is_rejected():
    # Arrange
    overrides = {"location": ""}
    # Act
    text = _refusal_text(**overrides)
    # Assert
    assert text != ""


def test_to_dict_emits_exactly_the_contract_keys():
    # Arrange
    hint = _valid()
    # Act
    payload = hint.to_dict()
    # Assert
    assert tuple(payload.keys()) == HINT_KEYS


def test_to_dict_round_trips_the_message():
    # Arrange
    hint = _valid(message="a specific remedy")
    # Act
    payload = hint.to_dict()
    # Assert
    assert payload["message"] == "a specific remedy"


def test_hint_is_frozen():
    # Arrange
    hint = _valid()
    # Act
    mutate = lambda: setattr(hint, "kind", "lint")  # noqa: E731
    # Assert
    with pytest.raises(Exception):
        mutate()


@pytest.mark.parametrize("kind", KINDS)
def test_every_declared_kind_is_constructible(kind):
    # Arrange
    overrides = {"kind": kind}
    # Act
    hint = _valid(**overrides)
    # Assert
    assert hint.kind == kind


@pytest.mark.parametrize("severity", SEVERITIES)
def test_every_declared_severity_is_constructible(severity):
    # Arrange
    overrides = {"severity": severity}
    # Act
    hint = _valid(**overrides)
    # Assert
    assert hint.severity == severity


# EOF
