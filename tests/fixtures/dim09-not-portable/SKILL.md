---
name: research-aggregator
version: 1.0.0
author: example-team
tags: [research, web, aggregation]
---

# Research Aggregator

## Description

Aggregate research on a topic from multiple sources and produce a structured briefing. Use this skill when the user asks to research a topic, gather information from the web, or produce a research briefing. Trigger on phrasings like "research this topic", "gather information on", "find out about", or "produce a briefing on". Do not trigger on requests to summarise a single document already in context.

## When to Use

**Trigger conditions:**
- "Research [topic] for me"
- "Gather information on …"
- "Find out about …"
- "Produce a briefing on …"
- "What can you find out about …?"

**Do not trigger when:**
- The user provides a document and asks for a summary (use document-summariser skill)
- The user asks for creative writing or opinion, not research

## Instructions

1. Dispatch a subagent to search the web for the topic using the `claude` CLI with a web search prompt. Use the command: `claude --tool web_search "search for: <topic>"`. Collect the results.

2. Open the browser to `https://scholar.google.com` and search for academic papers on the topic. Extract the top 5 results. If browser access is unavailable, skip this step and note the omission.

3. Dispatch a second subagent to search news sources. Use: `claude --tool web_search "news: <topic> site:reuters.com OR site:bbc.com"`. Collect the top 3 results.

4. Dispatch a third subagent to search for statistics and data. Use: `claude --tool web_search "<topic> statistics data 2024 2025"`. Collect the top 3 results.

5. Merge all results from the subagents. Deduplicate by URL. Rank by relevance.

6. For each source, open the browser to read the full article. Extract the key claims and data points.

7. Synthesise the findings into a structured briefing following the output contract below.

8. Use the `claude` CLI to run a final quality check: `claude --prompt "review this briefing for accuracy and completeness" --input <briefing>`.

## Output Contract

Produce a Markdown briefing:

```markdown
# Research Briefing: <topic>

**Date:** <ISO 8601 date>
**Sources consulted:** <count>

## Key Findings

- <Finding 1>
- <Finding 2>
- <Finding 3>

## Evidence

<Paragraph expansion of findings with citations.>

## Gaps

<Topics or questions that could not be answered from available sources.>

## Sources

| Title | URL | Type |
|-------|-----|------|
| ... | ... | academic / news / web |
```

## Examples

**Example 1 — technology topic:**

Input: "Research the current state of WebAssembly adoption in production systems."

Expected output: Briefing with 5+ key findings, evidence section citing 3–5 sources, gaps noting areas with limited public data, and a sources table.

**Example 2 — scientific topic:**

Input: "Find out about recent advances in mRNA vaccine platforms."

Expected output: Briefing draws on academic papers, news coverage, and official health organisation sources. Key findings focus on peer-reviewed evidence.

## Environment and Portability

This skill requires:
- Subagent dispatch capability via the `claude` CLI
- Browser access for full article reading and Google Scholar
- Web search tool access

## References

No bundled files.
