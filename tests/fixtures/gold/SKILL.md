---
name: document-summariser
version: 1.0.0
author: example-team
tags: [summarisation, documents, writing]
---

# Document Summariser

## Description

Summarise one or more documents into a structured brief. Use this skill when the user asks to summarise, condense, or produce an overview of a document, article, report, or set of files. Trigger on phrasings like "summarise this", "give me a summary of", "condense these docs", "TL;DR for", or "what does this document say". Do not trigger on requests to translate, rewrite, expand, or generate new content from scratch.

## When to Use

**Trigger conditions:**
- "Summarise [document/file/URL]"
- "Give me the key points from …"
- "TL;DR this report"
- "What does this say?" (when a document is attached or in context)
- "Condense these notes into …"
- "Create an executive summary of …"

**Do not trigger when:**
- The user asks to *expand*, *rewrite*, or *translate* content
- The user asks to generate a new document (use the document-drafter skill instead)
- The input is code to be explained (use the code-explainer skill instead)

## Instructions

1. Read each input document in full before summarising. Do not begin writing until you have read all provided documents, because later sections sometimes contradict earlier ones.

2. Identify the document type (report, article, meeting notes, specification, other) using the heuristics in `references/guide.md`. The type determines which summary template to apply.

3. Run `scripts/process.py --input <file> --type <type>` to extract structured metadata (word count, section headers, detected entities). Review the output before drafting the summary.

4. Produce the summary following the output contract below. Do not add commentary outside the contract fields.

5. If more than one document is provided, summarise each separately in its own `## Document N` block, then add a `## Cross-Document Themes` section.

## Output Contract

Produce a Markdown document matching this exact template:

```markdown
# Summary: <document title or filename>

**Type:** <report | article | meeting-notes | specification | other>
**Source:** <filename or URL>
**Word count:** <original word count>
**Date processed:** <ISO 8601 date>

## Key Points

- <Point 1>
- <Point 2>
- <Point 3 — add more as needed, minimum 3>

## Detail

<2–4 paragraph expansion of the key points. Each paragraph covers one main theme.>

## Gaps and Caveats

<Any areas where the source document was unclear, contradictory, or incomplete. Write "None identified" if clean.>
```

All fields are required. Do not omit `Gaps and Caveats` even if the document appears complete.

## Examples

**Example 1 — short article:**

Input: A 600-word blog post about container orchestration best practices.

Expected output: Key Points lists 4–5 practices, Detail covers 2 paragraphs on networking and storage separately, Gaps notes the article only covers Kubernetes and not Nomad.

**Example 2 — meeting notes:**

Input: A 1,200-word meeting transcript from a product planning session.

Expected output: Type is `meeting-notes`, Key Points lists decisions made (not discussion points), Detail covers each agenda item, Gaps notes action items whose owners were not recorded.

**Example 3 — multi-document:**

Input: Three quarterly reports from the same organisation.

Expected output: Three separate `## Document N` blocks each following the template, followed by `## Cross-Document Themes` identifying trends across quarters.

## Environment and Portability

This skill requires:

- **Python 3.9+** for `scripts/process.py`. If Python is unavailable, extract metadata manually: count words with the editor word-count tool, list section headers by scanning `#` lines.
- **File system read access** to the input documents. If documents are pasted inline rather than referenced as files, pass `--input -` to read from stdin, or skip the script step and note word count as "not available".

No network access is required. No files are written outside the session.

## Bundled Files

| File | Purpose |
|------|---------|
| `references/guide.md` | Document-type heuristics and classification rules |
| `scripts/process.py` | Metadata extraction script |
| `tests/test_eval.py` | Eval suite for grading summarisation quality |

## References

- See `references/guide.md` for full document-type classification rules.
- See `scripts/process.py --help` for script usage.
- See `tests/test_eval.py` for the eval suite.
