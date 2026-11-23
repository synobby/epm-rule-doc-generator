# GitHub issue for a v2 improvement (copy into GitHub → Issues → New issue)

**Title:** v2: Whole-application mode — document all rules from an LCM snapshot with a dependency map

**Labels:** `enhancement`, `v2`

**Body:**

## Problem
The MVP documents one rule at a time. A consultant taking over an application has 50–200 rules and needs to know how they relate: which form launches which rule, and which rules write to the same data.

## Proposal
- Upload a zipped LCM / migration snapshot.
- Parse every business rule (reuse `core/parser_calc.py` and `core/parser_groovy.py`).
- Generate documentation for each rule (batched, with progress bar and cost estimate).
- Build a dependency map: rule → FIX scope → members written; highlight overlapping write scopes.
- Export one combined technical design document (.docx) with a table of contents.

## Acceptance criteria
- [ ] Accepts a snapshot of up to 200 rules
- [ ] Shows progress and an estimated AI cost before running
- [ ] Dependency map viewable in the app and included in the export
- [ ] Rules with overlapping write scopes are flagged
- [ ] Tests for snapshot parsing with a sample (non-client) snapshot

## Out of scope
Connecting to a live EPM instance via REST API (separate issue).

---
**Command-line option** (if you use the GitHub CLI):
```bash
gh issue create --title "v2: Whole-application mode — document all rules from an LCM snapshot with a dependency map" --label enhancement --body-file docs/v2-issue.md
```
(Create the `v2` / `enhancement` labels first in GitHub if they don't exist.)
