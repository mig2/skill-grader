"""Unit tests for the PR collection script.

These cover the script. They say nothing about whether the skill triggers or
whether the changelog it writes is any good — that is what evals are for, and
this fixture deliberately ships none.
"""

from scripts.collect_prs import _fallback_from_git_log, collect


def test_fallback_returns_empty_on_git_failure(monkeypatch):
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("P", (), {"returncode": 1, "stdout": ""})(),
    )
    assert _fallback_from_git_log("v1", "v2") == []


def test_fallback_parses_merge_subjects(monkeypatch):
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "P", (), {"returncode": 0, "stdout": "Merge PR #1\nMerge PR #2\n"}
        )(),
    )
    result = _fallback_from_git_log("v1", "v2")
    assert len(result) == 2
    assert result[0]["labels"] == []


def test_collect_returns_list(monkeypatch):
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("P", (), {"returncode": 0, "stdout": "[]"})(),
    )
    assert collect("v1", "v2") == []
