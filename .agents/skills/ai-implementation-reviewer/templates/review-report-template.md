# Implementation Review: <system> - slice <Mx>

Plan: `<path>` v<n> · Implementation: `<path>` · Commit/hash: <hash or working tree> · Reviewer: <role/agent> · Date: <YYYY-MM-DD>
Independence: <I did not write any reviewed artifact | disclosure>

## Verdict: APPROVE / APPROVE WITH CONDITIONS / REJECT

One paragraph: why. **What would change this verdict:** ...
Permitted use if conditional: <non-production / shadow only / none>

## 1. Scorecard

| Dimension | Score 0-4 | Evidence (one line) |
| :-- | :-: | :-- |
| Guardrails and scope | | |
| Requirement coverage | | |
| Correctness | | |
| AI safety and quality | | |
| Security and privacy | | |
| Contracts | | |
| Test adequacy and honesty | | |
| Delivery and operations | | |
| Maintainability and docs | | |

Safety floor (min of guardrails, correctness, security, AI safety): <n> · Average of others: <n>

## 2. What I ran

| Check | Command | Result |
| :-- | :-- | :-- |
| Install + unit | | |
| Lint / type-check | | |
| Component / integration | | |
| ID trace | `plan_extract.py trace ...` | <covered>/<total> requirements, <covered>/<total> tests |
| Secret scan / `git status` | | |
| Re-run of hand-off claims | | |

Not run (and why): ...

## 3. Findings

| ID | Sev | Category | Location (`path:line`) | Evidence | Required change | Owner role |
| :-- | :-: | :-- | :-- | :-- | :-- | :-- |

Sorted most severe first. Categories: guardrail, correctness, ai-safety, security, contract, test, delivery, operations, maintainability, docs.

## 4. Guardrail verification

| Guardrail | Enforced at | Negative test | Reviewer check |
| :-: | :-- | :-- | :-: |

## 5. Requirement coverage matrix (slice)

| Req ID | Code | Test | Contract | Verified how | Status |
| :-: | :-- | :-- | :-- | :-- | :-: |

Status: Verified · Partial · Missing · Unverified

## 6. Strengths

- ...

## 7. Claims challenged

| Hand-off claim | Source file | Reproduced? | Note |
| :-- | :-- | :-: | :-- |

## 8. Review coverage and limits

Read in full: ... · Sampled: ... · Not reviewed: ... · Environment limits (no cloud, no real data, no live model): ...

## 9. Conditions for approval / next steps

1. ...
Suggested tracking commands (not run): `bd create "..." ...`

## 10. Re-review (append; do not rewrite earlier sections)

| Date | Findings re-checked | Result | Verdict now |
| :-- | :-- | :-- | :-- |
