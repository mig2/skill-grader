# Document Type Classification Guide

This guide defines the heuristics used by the document-summariser skill to classify input documents before selecting a summary template.

## Table of Contents

1. [Classification Overview](#classification-overview)
2. [Document Types](#document-types)
   - [Report](#report)
   - [Article](#article)
   - [Meeting Notes](#meeting-notes)
   - [Specification](#specification)
   - [Other](#other)
3. [Decision Tree](#decision-tree)
4. [Edge Cases](#edge-cases)

---

## Classification Overview

Classification is a pre-processing step. The type you assign determines which fields in the output template receive emphasis. Misclassification degrades summary quality but does not cause failure — if uncertain, use `other` and note the ambiguity in `Gaps and Caveats`.

Apply the decision tree in order. Stop at the first match.

---

## Document Types

### Report

**Signals:**
- Contains an executive summary, methodology, or findings section
- Has numbered sections or appendices
- References data sources, citations, or footnotes
- Formal register throughout

**Summary emphasis:** Key Points should capture findings and recommendations. Detail should cover methodology briefly and findings in depth.

### Article

**Signals:**
- Authored by a named individual or publication
- Narrative structure (introduction → argument → conclusion)
- Does not contain numbered sections or appendices
- May contain pull-quotes or sidebars

**Summary emphasis:** Key Points capture the main argument and supporting evidence. Detail follows the article's own narrative arc.

### Meeting Notes

**Signals:**
- Contains attendee list, date, or agenda
- Includes action items, owners, or due dates
- Conversational fragments or direct quotes
- May be a transcript

**Summary emphasis:** Key Points capture *decisions made* (not discussion), Detail covers agenda items. Flag unassigned action items in Gaps.

### Specification

**Signals:**
- Contains `MUST`, `SHOULD`, `MAY` language (RFC 2119)
- Defines interfaces, schemas, or protocols
- Versioned with a changelog section
- Highly structured with numbered requirements

**Summary emphasis:** Key Points capture the primary requirements. Detail describes the system being specified and key constraints. Flag any requirements with undefined terms in Gaps.

### Other

Use when none of the above types match clearly, or when the document is mixed (e.g., a report that reads like an article). Note the classification ambiguity in `Gaps and Caveats`.

---

## Decision Tree

```
Does the document contain an executive summary, methodology, or findings?
  YES → report
  NO ↓

Does it contain an attendee list, action items, or agenda?
  YES → meeting-notes
  NO ↓

Does it use MUST/SHOULD/MAY or define interfaces and schemas?
  YES → specification
  NO ↓

Is it authored narrative with introduction → argument → conclusion?
  YES → article
  NO → other
```

---

## Edge Cases

**Annual reports from companies:** Classify as `report` even if they read like articles in places. The presence of financial data and appendices is decisive.

**Transcripts without agenda:** Classify as `meeting-notes` if there are speakers and timestamps. If it reads more like an interview, use `article`.

**RFCs and standards documents:** Always `specification`, even if the RFC is informational.

**Blog posts with data:** Use `article`. The presence of charts or tables alone does not make something a `report`.
