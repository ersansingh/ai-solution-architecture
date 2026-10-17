# Observability, Runbooks, DR and Cost

## 1. Telemetry contract (agree with the developer's hand-off)

| Signal | Required content | Never include |
| :-- | :-- | :-- |
| Logs | JSON; timestamp, level, service, version, env, correlation_id, event, outcome, ids/hashes, durations | Secrets, PII, document content, full prompts/completions |
| Metrics | throughput, latency histograms, error rate by type, queue depth + oldest age, DLQ depth, decisions by outcome, review rate, model calls/tokens/cost, fallback usage, cache hit rate, policy/prompt/model version in use | High-cardinality labels (ids), PII |
| Traces | one trace per unit of work across components; spans for each external call with status | Payloads |
| Audit | immutable record of decisions, inputs' hashes, versions, reviewer actions | Anything editable after the fact |

Where the project uses the `ai-ml-observability-architect` design (OTel Gateway, Prometheus, Grafana, Observe), implement the collectors, dashboards and alert rules to that design instead of inventing a new stack.

## 2. SLO -> alert -> runbook map

Build a table from plan section 13 (and the design) and complete it:

| SLO / signal | Target (plan) | Metric / query | Alert (burn rate or threshold) | Severity | Runbook |
| :-- | :-- | :-- | :-- | :-: | :-- |

Standard AI-system signals to cover, if the plan has the matching requirement: end-to-end latency per document; queue age; DLQ non-empty; error budget burn; extraction/decision quality proxies (review rate, low-confidence rate, override rate by reviewers); drift (input distribution, score distribution); false auto-approve detected by audit sampling; model/provider errors and throttling; cost per unit and daily spend; evidence write failures; policy version mismatch; certificate/credential expiry.

Alert hygiene: every alert has an owner, a runbook link, a clear action; no alert without a runbook; page only on user-visible or data-integrity impact; tickets for the rest. Multi-window burn-rate alerts for SLOs.

## 3. Dashboards

Service overview (golden signals), pipeline flow (stage counts, queue ages, DLQ), model quality and cost, business outcomes (auto vs review vs rejected), infrastructure health, release markers. Dashboards as code, in the repo.

## 4. Runbooks

One per alert and per kill-switch/risk in plan section 14, using [`../templates/runbook-template.md`](../templates/runbook-template.md). Minimum set: DLQ growth/redrive, dependency outage and degraded mode, model provider throttling/outage (fallback and review-only), bad policy/prompt release (rollback), data correction/reprocessing, credential/OIDC expiry, evidence bundle verification failure, restore from backup, regional failover, cost spike. Each runbook is executable by someone who did not build the system: symptoms, impact, checks (commands), mitigation, rollback, escalation, verification, post-incident follow-up.

## 5. Backup, restore and DR

- Back up stateful stores per plan RPO (database snapshots, object versioning/replication, config and policy repos). State retention and encryption.
- **Restore test**: documented procedure and a dated result (RESTORED + time taken) or NOT TESTED. A backup never restored is an assumption.
- DR: RTO/RPO from plan; failover steps; data replication method; what is degraded; failback. Rehearsal status labelled.

## 6. Security operations

Patch/rebuild cadence for base images; dependency update bot; vulnerability SLAs; audit log retention; access reviews; secrets rotation schedule; incident process and who is paged.

## 7. Cost guardrails

- Budgets and alarms by environment and tag; model-spend metric with daily cap that triggers degrade-to-review or alert per plan.
- CI cost: estimate minutes per PR and nightly runs; caching and path filters; scheduled jobs frequency justified.
- Infrastructure sizing noted against the plan's TCO; flag deviations > the plan's tolerance.

## 8. Operational readiness review (before the reviewer)

- [ ] Every alert maps to a runbook; every runbook step is possible with granted access
- [ ] Dashboards load with real metric names from the code (checked against a local run)
- [ ] Log redaction verified on a sample run
- [ ] Restore and rollback rehearsed or explicitly marked not rehearsed
- [ ] Kill-switch tested in a non-production environment or marked not tested
- [ ] On-call, escalation and ownership named (or `TBD (owner)`)
