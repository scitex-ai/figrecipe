"""Tests for reading and writing the shared manuscript-hints feed.

The feed is written by three producers and read by a UI that treats malformed
as empty, so the behaviour under test is mostly about NOT destroying data:
foreign entries survive a merge, and an unparseable feed is refused rather
than overwritten. Real files on tmp_path, no mocks. One assertion per test,
AAA markers.
"""

from __future__ import annotations

import json

import pytest

from figrecipe._manuscript_hints._feed import (
    READ_ABSENT,
    READ_MALFORMED,
    READ_OK,
    FeedWriteRefused,
    feed_path,
    merge_by_source,
    read_feed,
    recompute_summary,
    write_feed,
)
from figrecipe._manuscript_hints._hint import Hint


def _hint(location="figures/fig01.png", kind="stale-recipe", severity="warning"):
    """A valid figrecipe hint."""
    return Hint(
        kind=kind,
        severity=severity,
        message="re-save this figure through figrecipe",
        claim_id="figures/fig01",
        location=location,
    )


def _foreign_entry(source="scitex-writer"):
    """An entry belonging to another producer, as it appears in the feed."""
    return {
        "source": source,
        "claim_id": "claims/intro",
        "kind": "citation",
        "severity": "info",
        "message": "unresolved citation",
        "location": "main.tex:12",
    }


def _write_raw(root, text):
    """Put arbitrary bytes at the feed path, creating parents."""
    path = feed_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def project(tmp_path):
    """An empty project root."""
    return tmp_path


def test_read_reports_absent_when_no_feed_exists(project):
    # Arrange
    expected = READ_ABSENT
    # Act
    result = read_feed(project)
    # Assert
    assert result.status == expected


def test_absent_feed_is_usable(project):
    # Arrange
    expected = True
    # Act
    result = read_feed(project)
    # Assert
    assert result.usable is expected


def test_read_reports_malformed_on_invalid_json(project):
    # Arrange
    _write_raw(project, "{not json at all")
    # Act
    result = read_feed(project)
    # Assert
    assert result.status == READ_MALFORMED


def test_malformed_feed_is_not_usable(project):
    # Arrange
    _write_raw(project, "{not json at all")
    # Act
    result = read_feed(project)
    # Assert
    assert result.usable is False


def test_malformed_read_explains_why(project):
    # Arrange
    _write_raw(project, "{not json at all")
    # Act
    result = read_feed(project)
    # Assert
    assert "invalid JSON" in (result.reason or "")


def test_read_reports_malformed_when_hints_is_not_a_list(project):
    # Arrange
    _write_raw(project, json.dumps({"hints": {"a": 1}}))
    # Act
    result = read_feed(project)
    # Assert
    assert result.status == READ_MALFORMED


def test_read_reports_malformed_when_hints_key_is_missing(project):
    # Arrange
    _write_raw(project, json.dumps({"schema": "manuscript-hints/1"}))
    # Act
    result = read_feed(project)
    # Assert
    assert "missing" in (result.reason or "")


def test_read_reports_ok_for_a_well_formed_feed(project):
    # Arrange
    _write_raw(project, json.dumps({"hints": [_foreign_entry()]}))
    # Act
    result = read_feed(project)
    # Assert
    assert result.status == READ_OK


def test_read_returns_the_existing_entries(project):
    # Arrange
    _write_raw(project, json.dumps({"hints": [_foreign_entry()]}))
    # Act
    result = read_feed(project)
    # Assert
    assert len(result.hints) == 1


def test_merge_keeps_entries_from_other_producers():
    # Arrange
    existing = [_foreign_entry()]
    # Act
    merged = merge_by_source(existing, [_hint()])
    # Assert
    assert _foreign_entry() in merged


def test_merge_replaces_our_own_previous_entries():
    # Arrange
    existing = [_hint(location="old.png").to_dict()]
    # Act
    merged = merge_by_source(existing, [_hint(location="new.png")])
    # Assert
    assert [entry["location"] for entry in merged] == ["new.png"]


def test_merge_preserves_entries_with_no_source_field():
    # Arrange
    existing = [{"message": "who wrote this?"}]
    # Act
    merged = merge_by_source(existing, [_hint()])
    # Assert
    assert {"message": "who wrote this?"} in merged


def test_summary_total_counts_every_entry():
    # Arrange
    entries = [_foreign_entry(), _hint().to_dict()]
    # Act
    summary = recompute_summary(entries)
    # Assert
    assert summary["total"] == 2


def test_summary_counts_by_severity():
    # Arrange
    entries = [_hint(severity="error").to_dict(), _hint(severity="error").to_dict()]
    # Act
    summary = recompute_summary(entries)
    # Assert
    assert summary["by_severity"]["error"] == 2


def test_summary_counts_by_kind():
    # Arrange
    entries = [_hint(kind="missing-recipe").to_dict()]
    # Act
    summary = recompute_summary(entries)
    # Assert
    assert summary["by_kind"]["missing-recipe"] == 1


def test_write_creates_the_feed_when_absent(project):
    # Arrange
    target = feed_path(project)
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert target.exists()


def test_write_stores_the_hint(project):
    # Arrange
    target = feed_path(project)
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert json.loads(target.read_text())["hints"][0]["source"] == "figrecipe"


def test_write_keeps_another_producers_hints(project):
    # Arrange
    _write_raw(project, json.dumps({"hints": [_foreign_entry()]}))
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert _foreign_entry() in json.loads(feed_path(project).read_text())["hints"]


def test_write_recomputes_the_summary_over_all_producers(project):
    # Arrange
    _write_raw(project, json.dumps({"hints": [_foreign_entry()], "summary": {"total": 99}}))
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert json.loads(feed_path(project).read_text())["summary"]["total"] == 2


def test_write_preserves_an_existing_schema_id(project):
    # Arrange
    _write_raw(project, json.dumps({"schema": "manuscript-hints/7", "hints": []}))
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert json.loads(feed_path(project).read_text())["schema"] == "manuscript-hints/7"


def test_write_refuses_a_malformed_feed(project):
    # Arrange
    _write_raw(project, "{truncated")
    # Act
    attempt = lambda: write_feed(project, [_hint()])  # noqa: E731
    # Assert
    with pytest.raises(FeedWriteRefused):
        attempt()


def test_refused_write_leaves_the_original_bytes_untouched(project):
    # Arrange
    _write_raw(project, "{truncated")
    # Act
    try:
        write_feed(project, [_hint()])
    except FeedWriteRefused:
        pass
    # Assert
    assert feed_path(project).read_text() == "{truncated"


def test_refusal_names_the_offending_path(project):
    # Arrange
    _write_raw(project, "{truncated")
    # Act
    try:
        write_feed(project, [_hint()])
        text = ""
    except FeedWriteRefused as exc:
        text = str(exc)
    # Assert
    assert str(feed_path(project)) in text


def test_write_leaves_no_temp_files_behind(project):
    # Arrange
    write_feed(project, [_hint()])
    # Act
    leftovers = list(feed_path(project).parent.glob(".hints-*"))
    # Assert
    assert leftovers == []


def test_rewriting_is_idempotent(project):
    # Arrange
    write_feed(project, [_hint()])
    first = feed_path(project).read_text()
    # Act
    write_feed(project, [_hint()])
    # Assert
    assert feed_path(project).read_text() == first


# EOF
