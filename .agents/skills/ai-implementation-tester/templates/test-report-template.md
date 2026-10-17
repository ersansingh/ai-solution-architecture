# Test Report: <system> - slice <Mx>

Plan: `<path>` v<n> · Commit/hash tested: <hash or "working tree"> · Author role: tester · Date: <YYYY-MM-DD>
Environment: <local compose / staging> · Data: SYNTHETIC / REAL · Models: fake / recorded / live

**Verdict: PASS / FAIL / BLOCKED (partial)** - one-sentence reason.

## 1. Summary by level

| Level | Planned | Written | Run | Pass | Fail | Blocked | Command |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: | :-- |
| Unit (dev + gap-fill) | | | | | | | |
| Component | | | | | | | |
| Integration | | | | | | | |
| Contract | | | | | | | |
| End-to-end | | | | | | | |
| AI evaluation | | | | | | | |
| Fault / resilience | | | | | | | |
| Security | | | | | | | |
| Performance smoke | | | | | | | |

Coverage (branch): core <x%>, gate/money <x%> · Mutation score on gate/rules: <x%> or NOT RUN

## 2. Result per plan Test ID

| Test ID | Level | Req IDs | File | Result | Evidence (counts / metric vs threshold) |
| :-: | :-- | :-- | :-- | :-: | :-- |

Result values: PASS · FAIL · BLOCKED (reason) · NOT WRITTEN (reason) · NOT RUN (reason)

## 3. Guardrail verification

| Guardrail | Negative test | Result |
| :-: | :-- | :-: |

## 4. AI evaluation results

| Metric | Target (plan) | Measured | 95% CI | Slice | Dataset (REAL/SYNTHETIC) | Versions |
| :-- | :-: | :-: | :-: | :-- | :-: | :-- |

Adversarial pack: <n> cases, <n> violations. Determinism: <n> runs identical / differences listed.

## 5. Defects

| ID | Sev | Req / guardrail | Level found | Minimal repro | Expected | Actual | Suspected component |
| :-- | :-: | :-- | :-- | :-- | :-- | :-- | :-- |

## 6. Coverage honesty (what this report does NOT show)

- ...

## 7. Flaky / quarantined

| Test | Seed | Runs | Failures | Task ID |
| :-- | :-: | :-: | :-: | :-: |

## 8. Re-run commands

```text
<one per level>
```

## 9. Independence statement

Production code changed by tester: none (`git status` evidence: <paste>). Expected values derived from: <requirements / contracts / hand calculations>.
