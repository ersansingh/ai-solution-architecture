# Hand-off Contracts Between Roles

Each hand-off is a file in `implementation/handoff/`. A receiving role must refuse (and say why) if the hand-off is missing its required parts.

## Common header (every hand-off file)

```markdown
Plan: <path> v<n> · Slice: <milestone, task ids> · Author role: <role> · Date: <YYYY-MM-DD>
Status vocabulary: RAN (command + result shown) · READ (inspected, not run) · ASSUMED
```

## 1. developer -> tester (`developer-handoff.md`)

Required:
- **Built**: component -> path -> requirement IDs -> contract it implements.
- **Stubbed / not built**: item, why, which task replaces it.
- **How to run**: install, run locally, run unit tests, lint, type-check, and the exact commands, each marked RAN with the result.
- **Contracts**: paths of OpenAPI/AsyncAPI/JSON Schema/policy files and their versions.
- **Config and environment variables**: name, purpose, default, secret yes/no.
- **Known limits and edge cases handled / not handled.**
- **Fixtures and seed data**: synthetic only, how to regenerate.
- **Plan deviations**.

Tester refuses if: no run commands, no contracts for a service boundary, or "tests pass" without output.

## 2. tester -> developer (defect list) and -> reviewer (`test-report.md`)

Required:
- Table per plan test ID: level, requirement IDs, file, result (PASS / FAIL / BLOCKED / NOT WRITTEN), evidence (command, counts).
- **Defects**: ID, severity, requirement/guardrail broken, minimal repro, expected vs actual, suspected component (not a patch).
- **Coverage honesty**: what the suite cannot show (no real cloud, synthetic data only, model stubbed).
- Flaky tests, with seeds and run counts.
- Commands to re-run each level.

Developer refuses to "fix" by changing tests; a test changes only if the requirement or contract it was derived from changed (state which).

## 3. developer + tester -> devops (`devops-handoff.md` input is both files)

DevOps needs: run commands per level (so CI mirrors them), runtime and dependency versions, container needs, environment variables and secrets list (names only), required cloud resources per component, health/readiness endpoints, log fields and metrics emitted, expected SLOs from plan section 13.

DevOps refuses if: commands are not reproducible from a clean checkout, or secrets would have to be hard-coded.

## 4. devops (`devops-handoff.md`)

Required:
- Pipelines: file, triggers, jobs, required checks, promotion path, approvals.
- IaC: modules, what validated (fmt / validate / lint / security scan / plan) and the result of each, what was **not** applied.
- Environments and config differences; secret names and where they live (never values).
- Release and rollback procedure, with rehearsal status (RAN or NOT REHEARSED).
- Observability: dashboards, alerts mapped to SLOs, log redaction check.
- Runbooks written and what each covers; on-call assumptions.
- Cost estimate or guardrails (budgets, usage alarms) vs plan.

## 5. all -> reviewer

The reviewer reads the plan, the code and the files above; hand-off prose is a map, not evidence. It must be able to re-run at least the unit and one integration command from a clean checkout.

## 6. reviewer -> owners (`review-report.md`)

Required: verdict, scorecard, findings (ID, severity, category, file:line, evidence, required change, owner role), requirement and guardrail coverage matrix, what the reviewer ran, what it could not verify, conditions for approval.

## Severity scale (shared)

| Sev | Meaning | Effect |
| :-: | :--- | :--- |
| Blocker | Guardrail violated, data loss/corruption, secret exposure, wrong money/decision outcome, build cannot run | Reject |
| High | Requirement unmet, missing error handling on a boundary, untested critical path, unsafe default | Fix before approval |
| Medium | Maintainability, partial coverage, missing runbook detail | Fix or accept with owner and date |
| Low | Style, naming, minor docs | Optional |
