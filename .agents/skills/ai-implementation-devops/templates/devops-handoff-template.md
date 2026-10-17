# DevOps Hand-off: <system> - slice <Mx>

Plan: `<path>` v<n> · Slice: <milestone, task IDs> · Author role: devops · Date: <YYYY-MM-DD>
Status vocabulary: **RAN** · **READ** · **NOT RUN (reason)** · **ASSUMED**. Nothing in this file was applied or deployed unless stated as user-confirmed.

## 1. Gap analysis

| Item | Design/diagram says | IaC/pipeline has | Code needs | Gap / action | Sev |
| :-- | :-- | :-- | :-- | :-- | :-: |

Infra-level guardrails checked: <guardrail -> where enforced -> evidence>

## 2. Pipelines

| File | Triggers | Jobs | Required checks | Calls (make targets) | Validated by |
| :-- | :-- | :-- | :-- | :-- | :-- |

Deploy jobs: written, **disabled** until `ENABLE_DEPLOY=true`. Promotion path: <dev -> staging -> prod>, approvals: <env protections>.

## 3. Infrastructure as Code

| Check | Command | Result |
| :-- | :-- | :-- |
| fmt | | |
| init (no backend) | | |
| validate | | |
| tflint | | |
| security scan | | |
| guardrail policies | | |
| plan | | NOT RUN (no credentials) |

Resources added/changed: <list>. State backend: <defined / bootstrap documented>. Apply: NOT DONE.

## 4. Release and rollback

- Strategy: <shadow / canary / blue-green>; flags and kill-switches: <names, where set>
- Rollback procedure: <path> · Rehearsal: REHEARSED (<date, evidence>) / NOT REHEARSED
- Migration rule: <expand/contract summary>

## 5. Observability and operations

| SLO / signal | Metric | Alert | Severity | Runbook |
| :-- | :-- | :-- | :-: | :-- |

Dashboards: <paths>. Log redaction check: <RAN/READ>. Backup restore test: <RESTORED in X / NOT TESTED>. DR: <status>.

## 6. Cost

CI minutes per PR / nightly (estimate): <...> · Cloud budget alarms: <...> · Model spend cap: <...> · Deviation from plan TCO: <...>

## 7. What the user must do to go live (not done by me)

1. Create OIDC role(s) with trust limited to <repo/env>; set repository variables: <names>.
2. Create secrets by name in <secret manager>: <names>.
3. Configure environment protection (reviewers) for staging and prod.
4. Move/approve workflows from `implementation/.github/workflows/` to the repo root.
5. Enable deploy: set `ENABLE_DEPLOY=true` when ready.

## 8. Deviations and open items

| ID | Item | Plan says | Done instead | Approver |
| :-- | :-- | :-- | :-- | :-- |
