# Review Checklist, Scoring and Verdict Rules

Mark each item: OK (evidence) · FINDING (id) · N/A (reason) · UNVERIFIED (reason).

## L1 Guardrails and scope (stop-the-line)

- [ ] Each plan guardrail (section 1) has an enforcement point: permission absent, field not exposed, gate function, write-once store
- [ ] Each guardrail has a **negative** test that would fail if the guardrail were removed
- [ ] No code path can: move money / post to ledger / approve payments (if excluded), modify source documents, create or amend upstream records, declare fraud, expose a UI that the plan excludes
- [ ] IAM/permission lists contain no forbidden action; wildcard actions/resources absent or justified
- [ ] No out-of-scope feature built; no in-scope requirement of the slice silently dropped

## L2 Requirement coverage

- [ ] For each in-slice requirement: code location, test location, contract entry
- [ ] Tests assert the requirement's behaviour (not just that code runs)
- [ ] Trace script output reviewed; MISSING IDs explained or raised
- [ ] Deviations from the plan recorded with approver; stubs listed with replacing task

## L3 Correctness

- [ ] Money: integer minor units or Decimal, explicit rounding from policy, currency never implicit, no float anywhere in the path
- [ ] State machine: only allowed transitions; terminal states immutable; versions append-only where plan says
- [ ] Idempotency: replay of event/request yields one effect; keys derived deterministically
- [ ] Concurrency: unique constraints, conditional writes or locks; no check-then-act races
- [ ] Error handling: typed errors, no bare/silent except, retries bounded with jitter, non-retryable not retried
- [ ] Boundary validation against schemas; unknown versions fail closed
- [ ] Time handling UTC-aware; clock injectable; no `now()` in pure logic
- [ ] Resource limits: payload size, page counts, concurrency, memory; streams closed
- [ ] Determinism: same inputs/config -> same decision

## L4 AI safety and quality

- [ ] Model output parsed against schema; failure typed and routed safely
- [ ] Grounding: every value traceable to source; absence yields `unavailable`, not invention
- [ ] Prompt-injection handling: content delimited as data; no state-changing tools without allow-list and gate; security event logged
- [ ] Single auto-decision gate with allow-list; all other paths only escalate
- [ ] Fallback chain configurable and recorded in output; review-only kill-switch exists
- [ ] Prompts, policies, thresholds versioned data; business policy separated from tuned thresholds; no invented business numbers
- [ ] Evaluation hooks use production path; metrics named as in plan
- [ ] Claims of accuracy labelled REAL vs SYNTHETIC; gate closure only with REAL
- [ ] Cost and latency telemetry per call; budgets enforced

## L5 Security and privacy

- [ ] AuthN/AuthZ on every operation; scopes least-privilege; tenant isolation checked in code and tests
- [ ] No secrets in code, config, fixtures, logs, prompts, test output, IaC state outputs (scan evidence)
- [ ] PII/document content absent from logs and metrics labels; redaction tested
- [ ] Injection classes handled (SQL, path traversal, SSRF, log/CRLF, deserialisation)
- [ ] Dependencies pinned and audited; container non-root, minimal, scanned
- [ ] Encryption at rest/in transit configured in IaC; public access blocked; logging/audit enabled; retention per plan

## L6 Contracts

- [ ] OpenAPI/AsyncAPI/JSON Schema valid and **match** the running code (diff or contract test)
- [ ] Error model uniform; idempotency and pagination defined; examples valid
- [ ] Versioning and compatibility rules stated; breaking changes flagged
- [ ] External contracts unmodified; gaps documented for approval

## L7 Test adequacy and honesty

- [ ] Pyramid: many fast unit, fewer component/integration, few E2E; each real boundary has an integration test
- [ ] Oracles independent (requirements, hand calculations); no snapshot of current output used as truth without justification
- [ ] Assertions meaningful (no `assert True`, no only-status-code checks where body matters)
- [ ] Mocks only at true external edges; the unit under test is never mocked
- [ ] Deterministic, hermetic, isolated; network guard present; no real data or accounts
- [ ] Failure and fault paths covered (timeouts, duplicates, crashes, concurrency)
- [ ] Test report numbers reproduce on a fresh run; flaky/quarantined items tracked
- [ ] Mutation sampling or manual mutation of gate/money code shows tests fail when logic is broken

## L8 Delivery and operations

- [ ] Workflow permissions least-privilege; actions pinned; timeouts; concurrency; no secrets on command lines; fork PR safety
- [ ] Pipeline calls documented make targets; stages and gates match plan section 12
- [ ] Deploy jobs disabled/approval-gated; OIDC only; build-once-promote; smoke test; rollback path
- [ ] IaC: validated, scanned, modules per diagram container, remote state with locking, tags, `prevent_destroy` on stateful resources, no apply performed
- [ ] Observability: telemetry contract implemented in code; SLO alerts exist and each links a runbook; dashboards use real metric names
- [ ] Runbooks executable; kill-switch documented; backup/restore and DR status honest
- [ ] Cost guardrails (budgets, model spend cap, CI minutes) present

## L9 Maintainability and docs

- [ ] Layout matches plan section 9; names and boundaries match the design components
- [ ] Cohesion, no god modules, no dead code, no commented-out blocks, TODOs linked to task IDs
- [ ] README works from a clean checkout; config documented
- [ ] Hand-offs truthful: commands, versions, env vars agree across files
- [ ] ADR/deviation records present for non-trivial choices

## Scorecard (0-4)

| Score | Meaning |
| :-: | :-- |
| 4 | Exemplary: verified by running and reading, no material issues |
| 3 | Sound: minor issues only |
| 2 | Partial: gaps that need fixing before production use |
| 1 | Weak: significant defects or mostly unverified |
| 0 | Absent or contradicted by evidence |

Dimensions: Guardrails · Requirement coverage · Correctness · AI safety · Security/privacy · Contracts · Test adequacy · Delivery/ops · Maintainability/docs. Overall = lowest of Guardrails, Correctness, Security, AI safety (a chain is as strong as its weakest safety link), reported next to the average of the rest.

## Verdict rules

- **REJECT** if: any Blocker; Guardrails score < 3; Correctness or Security score < 2; hand-off claims fail to reproduce; build/test cannot run from clean checkout.
- **APPROVE WITH CONDITIONS** if: no Blocker, all safety dimensions >= 2, High findings exist (each with owner and a re-review requirement). Allowed use: non-production / shadow only.
- **APPROVE** if: no Blocker/High, safety dimensions >= 3, Medium findings owned and dated, evidence reproducible.
- Always state **what would change the verdict**.

## Frequent defects to look for in AI-system builds

1. Tolerance or threshold hard-coded or defaulted by the developer instead of loaded from approved policy.
2. Auto-approve condition scattered across modules (several places can approve).
3. Float used for money in one overlooked path (CSV export, aggregation, JSON).
4. Retry on non-idempotent call without key; duplicate effect on redelivery.
5. Model JSON parsed with a permissive fallback that fills missing fields with defaults.
6. Logs include document text, prompt or completion.
7. Tests copy the implementation's output as expected values.
8. Mocks replace the database/queue in "integration" tests.
9. Terraform grants `*` on resources/actions "for now"; state bucket not encrypted or locked.
10. Workflow with `pull_request_target` plus checkout of PR code, or secrets available to forks.
11. Evaluation claimed on synthetic data but written as a real accuracy figure.
12. README commands that only work on the author's machine.
