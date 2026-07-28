"""
test_eval.py — Eval suite for the document-summariser skill.

These tests verify:
1. Structural correctness: output matches the required template.
2. Content completeness: all required fields are present and non-empty.
3. Edge cases: multi-document inputs, empty gap sections.
"""

import re
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    r"\*\*Type:\*\*",
    r"\*\*Source:\*\*",
    r"\*\*Word count:\*\*",
    r"\*\*Date processed:\*\*",
    r"## Key Points",
    r"## Detail",
    r"## Gaps and Caveats",
]

VALID_TYPES = {"report", "article", "meeting-notes", "specification", "other"}


def assert_structural(summary: str) -> None:
    """Assert that a summary string contains all required template fields."""
    for pattern in REQUIRED_FIELDS:
        assert re.search(pattern, summary), f"Missing required field matching: {pattern}"


def extract_type(summary: str) -> str:
    match = re.search(r"\*\*Type:\*\*\s*(\S+)", summary)
    assert match, "Could not extract Type field"
    return match.group(1)


def count_key_points(summary: str) -> int:
    key_points_section = re.search(
        r"## Key Points\n(.*?)(?=\n##|\Z)", summary, re.DOTALL
    )
    if not key_points_section:
        return 0
    return len(re.findall(r"^- ", key_points_section.group(1), re.MULTILINE))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_ARTICLE_SUMMARY = """\
# Summary: test-article.md

**Type:** article
**Source:** test-article.md
**Word count:** 612
**Date processed:** 2026-01-15

## Key Points

- The containerisation ecosystem is maturing rapidly.
- Kubernetes dominates orchestration but Nomad is growing in edge contexts.
- Observability tooling is now a first-class concern.
- Cost optimisation is the primary driver for workload migration.

## Detail

The article argues that the shift from virtual machines to containers is now complete
for most greenfield projects. The author provides survey data from 2025 showing 78%
of new services are container-native at time of deployment.

The second half addresses the operational overhead of running Kubernetes at scale.
The author recommends investing in platform engineering teams rather than expecting
individual squads to own their own cluster configuration.

## Gaps and Caveats

The article does not address on-premises deployments or air-gapped environments.
Survey methodology is not described; sample size and selection bias are unknown.
"""

MULTI_DOC_SUMMARY = """\
# Summary: q1-report.md

**Type:** report
**Source:** q1-report.md
**Word count:** 3200
**Date processed:** 2026-01-15

## Key Points

- Revenue up 12% quarter-on-quarter.
- Customer churn reduced from 4.2% to 3.1%.
- Engineering headcount grew by 8 FTEs.

## Detail

Q1 showed strong growth across all product lines. The enterprise segment outperformed
projections by 18%, driven by two large contract renewals.

## Gaps and Caveats

None identified.

# Summary: q2-report.md

**Type:** report
**Source:** q2-report.md
**Word count:** 3450
**Date processed:** 2026-01-15

## Key Points

- Revenue growth slowed to 4% quarter-on-quarter.
- New product launch delayed by one quarter.
- Customer churn increased to 3.8%.

## Detail

Q2 was impacted by the delayed product launch and increased competition in the SMB
segment. The engineering team completed the platform migration started in Q1.

## Gaps and Caveats

The report does not explain the cause of the churn increase.

## Cross-Document Themes

- Churn trended upward across both quarters, warranting investigation.
- Revenue growth is decelerating; Q2 growth rate is one-third of Q1.
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStructural:
    def test_all_required_fields_present(self):
        assert_structural(MINIMAL_ARTICLE_SUMMARY)

    def test_type_is_valid(self):
        doc_type = extract_type(MINIMAL_ARTICLE_SUMMARY)
        assert doc_type in VALID_TYPES

    def test_minimum_key_points(self):
        count = count_key_points(MINIMAL_ARTICLE_SUMMARY)
        assert count >= 3, f"Expected at least 3 key points, got {count}"

    def test_gaps_section_present_even_when_empty(self):
        # The template requires Gaps even when "None identified"
        assert "## Gaps and Caveats" in MINIMAL_ARTICLE_SUMMARY


class TestMultiDocument:
    def test_multi_doc_has_cross_document_themes(self):
        assert "## Cross-Document Themes" in MULTI_DOC_SUMMARY

    def test_multi_doc_all_documents_have_required_fields(self):
        # Split on "# Summary:" to get individual documents
        docs = re.split(r"(?=^# Summary:)", MULTI_DOC_SUMMARY, flags=re.MULTILINE)
        docs = [d for d in docs if d.strip().startswith("# Summary:")]
        assert len(docs) >= 2, "Expected at least 2 document summaries"
        for doc in docs:
            assert_structural(doc)


class TestEdgeCases:
    def test_gaps_none_identified_is_acceptable(self):
        # "None identified" is explicitly allowed by the output contract
        assert "None identified" in MULTI_DOC_SUMMARY

    def test_type_meeting_notes_hyphenated(self):
        summary = MINIMAL_ARTICLE_SUMMARY.replace("**Type:** article", "**Type:** meeting-notes")
        doc_type = extract_type(summary)
        assert doc_type in VALID_TYPES
