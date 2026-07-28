# Issue Import Guide

## Quick Import

Import all issues from `issues.json`:

```bash
cat issues.json | jq -c '.[]' | while read issue; do
  gh issue create \
    --title "$(echo "$issue" | jq -r '.title')" \
    --body "$(echo "$issue" | jq -r '.body')" \
    --label "$(echo "$issue" | jq -r '.labels | join(",")')"
done
```

## Label Setup

Create labels before first import:

```bash
# Severity labels
for sev in blocker major; do
  gh label create "severity:$sev" \
    --color "$([ "$sev" = blocker ] && echo d73a4a || echo e4e669)" \
    --description "skill-grader: $sev severity finding"
done

# Dimension labels
for dim in description-triggering trigger-surface progressive-disclosure \
           resource-hygiene script-vs-prose instructional-voice \
           output-contract examples environment-portability \
           least-surprise-safety testability; do
  gh label create "dim:$dim" --color c5def5 \
    --description "skill-grader: $dim dimension"
done
```

## Deduplication

Each issue body contains a stable fingerprint marker: `<!-- sg:<hash> -->`.

The hash is derived from: skill name, dimension number, location, and normalised problem text. Re-runs with the same findings produce the same fingerprints.

### Before importing, check for existing issues:

```bash
FINGERPRINT="sg:abc123..."
if gh issue list --state open --json body -q ".[].body" | grep -q "$FINGERPRINT"; then
  echo "Issue already exists, skipping"
fi
```

### Resolved findings

Findings that no longer reproduce on a re-run are reported as *resolved* in the delta section of the grade report. They are NOT auto-closed as GitHub issues — closing is a human decision.

## CSV Import

For tools that prefer CSV:

```bash
# issues.csv has columns: title, body, labels
# Labels are semicolon-separated
```

The CSV format is compatible with GitHub's issue importer and similar tools.
