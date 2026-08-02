# Label to Change-Type Mapping

Maps pull-request labels onto changelog sections. Labels are the classification
signal because PR titles are too inconsistent to parse reliably.

| Label | Section |
|-------|---------|
| `breaking` | Breaking changes |
| `feature`, `enhancement` | Features |
| `bug`, `fix`, `regression` | Fixes |
| `chore`, `refactor`, `deps`, `ci` | Internal |
| `docs` | Internal |

## Unlabelled pull requests

A PR with none of the above labels goes to **Internal**, and the run reports
how many landed there. A large unlabelled count means the mapping is drifting
from how the team actually labels, not that the changelog is complete.

## Multiple matching labels

Take the highest-precedence section, ordered as the table reads top to bottom.
A PR labelled both `breaking` and `bug` is a breaking change — readers need to
see it in the section that affects their upgrade.
