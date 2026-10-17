# Planning Heuristics for AI System Builds

## 1. Order work by risk, not by architecture layer

Put the cheapest test of the riskiest assumption first. For most AI systems the ranking is:

1. Access to real data and source systems (permissions, API, quality).
2. Decisions only the business can make (policies, tolerances, thresholds, retention).
3. Model/extraction quality on **real** samples, not synthetic ones.
4. Integration with the existing system and contract.
5. Non-functional targets (latency, throughput, cost).
6. Polish, dashboards, optimisation.

Align milestones with the funding gates from the strategy document when it exists: each gate's milestone and kill-switch becomes the exit criterion and continue/stop rule of one plan milestone.

## 2. Milestone archetypes (adapt, merge or drop)

| Milestone | Goal | Typical exit criteria |
| :--- | :--- | :--- |
| **M0 Foundations & decisions** | Access, accounts, repo, CI skeleton, decision log, data/sample audit | Real samples profiled; access works; blocking decisions scheduled with owners; gap table closed or owned |
| **M1 Data & evaluation harness** | Data contracts, ingestion, golden set, baseline model, metrics code | Golden set labelled and frozen; baseline score recorded; harness runs in CI |
| **M2 Walking skeleton** | Thinnest end-to-end path through every layer with stubs | One document/record flows source → result → API in a dev environment; idempotent replay works |
| **M3 Core capability** | Real models/rules for the main paths | Targets met on the golden set; zero violations of the "must never" rules |
| **M4 Hardening** | Fallbacks, retries, security, observability, cost controls, load/fault tests | Fault-injection and security tests pass; SLO dashboards live; runbooks written |
| **M5 Shadow / pilot** | Run beside the existing process without acting | Agreement rate and override rate within thresholds; no unsafe outcomes |
| **M6 Controlled go-live** | Enable automation for the safe subset | Approval by owners; rollback rehearsed; monitoring and on-call active |
| **M7 Continuous improvement** | Feedback loop, retraining, new sources | Drift triggers tested; quarterly review scheduled |

A milestone with no measurable exit criterion is not a milestone.

## 3. Task table conventions

`ID (M3-07) | Task | Owner role (developer/tester/devops/data/AI/business) | Depends on | Estimate (range) | Requirement / ADR / diagram page | Done when`

- One task = one reviewable outcome, 0.5-5 working days. Split larger ones.
- Task IDs are stable; reordering never renumbers.
- Every task has a "done when" that a second person could check.

## 4. Estimation

- Give ranges (best-likely-worst or low-high) and the basis: similar work, spike, vendor docs.
- Add an explicit uncertainty factor to tasks that depend on unseen data or unsigned decisions.
- Convert to calendar weeks only with a stated team size and focus factor (default 0.6-0.7 of nominal for mixed run/build teams). If team size is unknown, say "effort X-Y person-days; calendar depends on team size".
- Never reuse the financial model's cost numbers as the plan's estimates without saying they are planning figures.

## 5. Test strategy for AI systems (map each to requirement IDs)

| Layer | What it proves | Notes |
| :--- | :--- | :--- |
| Unit / property | Pure logic (money maths, normalisers, tolerance rules, state transitions) | Property tests for invariants (totals, idempotency, ordering) |
| Golden-set / model evaluation | Accuracy, calibration, coverage on frozen real samples | Split by group (supplier, customer) and by time; CI gate fails on regression |
| Contract | API and event schemas, data contracts | Consumer-driven where a downstream team exists |
| Integration | Real boundaries (queue, DB, object store, model endpoint, source API) | Use local emulators or a sandbox account; mocks only at true third-party edges |
| Fault injection | Timeouts, throttling, partial failure, duplicate delivery, poison messages | Prove retries, DLQ, circuit breaker, fallback chain |
| Security & AI safety | AuthZ, secret handling, PII in logs, prompt-injection-style content in inputs, least-privilege IAM | Include "forbidden capability absent" checks |
| Performance & cost | Throughput, p95 latency, cost per unit | Against agreed targets only |
| Shadow acceptance | Agreement with the existing process, override rate, unsafe-outcome count | Exit gate for go-live |

State the pass threshold for each gate and who signs it.

## 6. Environment and release plan

- Environments: dev, staging, prod (plus DR) with what differs (scale, data, approvals).
- IaC: what exists, what is missing vs the infrastructure page, state backend, drift detection.
- CI/CD: required checks, promotion rules, manual approvals, secrets via OIDC/roles (no static keys).
- Release: feature flags or review-only mode, canary by segment, rollback steps, migration order, data backfill and reprocessing rules.
- Run readiness: dashboards, alerts mapped to SLOs, runbooks, on-call, DLQ redrive, backup/restore test dates.

## 7. Risk register

Columns: ID, risk, likelihood, impact, trigger/early signal, mitigation, owner, milestone where it is retired. Add a **kill / pivot rule** for the top 3 risks (for example "if critical-field accuracy < threshold after two tuning sprints, switch extractor or narrow scope").

## 8. Definition of done (per task and per milestone)

Code reviewed; tests written and passing in CI; telemetry present with no secrets; docs/runbook updated; traceability row updated; verified by a run, not by belief.
