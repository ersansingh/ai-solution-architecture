# Test Levels Guide and Recipes

Python/pytest examples; translate to the project's stack. Folder: `tests/{unit,component,integration,contract,e2e,eval,fault,security,perf}/`.

## 1. Harness

- `tests/conftest.py`: fixtures for settings, clock, id generator, temp dirs, fake/real adapter selection (`--adapters=fake|local|live`; `live` is refused unless an env var the user set explicitly is present).
- `tests/compose.yaml` (or Testcontainers): database, queue (ElasticMQ/LocalStack SQS or RabbitMQ), object store (MinIO/LocalStack S3), HTTP mock (WireMock/MockServer/`respx`), optional OpenSearch. Pin image tags.
- Network guard: a session fixture that fails any test attempting to resolve a non-local host (`pytest-socket` or equivalent). Assert `AWS_ACCESS_KEY_ID` etc. are unset or point to local emulators.
- Seed data: `scripts/seed.py --seed 1234` generates synthetic documents/records deterministically. Label `FAKE`.
- Markers: `req("BR-07")`, `test_id("T-05")`, `unit`, `component`, `integration`, `e2e`, `eval`, `fault`, `security`, `perf`, `slow`. CI selects by marker.
- Helpers for polling: `eventually(assertion, timeout=10, interval=0.1)`; no fixed sleeps.

## 2. Unit review and gap-fill

Checklist per module: boundary values on both sides of every threshold; empty/None/oversize inputs; each branch of the decision gate; each error type; property tests for invariants (sum of parts, idempotence, order independence, monotonic tolerance). Run coverage with branch coverage and read the uncovered lines, not just the number. Mutation testing on `gate`/`rules`/`money`: any surviving mutant is a missing assertion.

## 3. Component tests

A component test starts **one** component through its real entry point (handler, HTTP app via `TestClient`, CLI) with its real internals, and fakes only its ports.

- Feed every contract example (valid) and a table of invalid variants (missing field, wrong type, extra field, oversize, wrong version).
- Assert output against the contract schema and the requirement, plus emitted events, logs (no secrets), metrics.
- Exercise each error path declared in the contract (status code, error code, retryable flag).
- Dependency failure through fake ports: timeout, 429, 5xx, malformed response -> expected retry/degrade/escalate behaviour.

## 4. Integration tests (real boundaries)

One scenario per boundary in the architecture diagram:

| Boundary | Must prove |
| :--- | :--- |
| Producer -> queue -> consumer | Message schema valid; at-least-once duplicate yields one effect; poison message lands in DLQ with reason; visibility timeout shorter than processing does not double-apply |
| Worker -> database | Constraints enforced; transaction rollback on failure; concurrent workers on same key resolve correctly; migrations apply forward on a populated database |
| Worker -> object store | Write-once honoured; checksum verified; overwrite refused; partial upload not visible |
| Component -> model adapter | Request/response shape; schema failure handled; timeout -> fallback; cost/latency telemetry emitted |
| Adapter -> external API | Contract pinned; 4xx/5xx/429 semantics; idempotent retry with same key; no unapproved call shape |
| Policy store -> engine | Version selection by effective date; unknown version fails closed |
| Workflow -> human task | Task created with reason codes; timeout escalates; decision recorded and fed back |

Use real containers for the infrastructure the plan names; use the cloud-emulator (LocalStack etc.) only for services it supports faithfully and say where fidelity is limited.

## 5. Contract tests

- **Spec validity**: lint OpenAPI/AsyncAPI/JSON Schema.
- **Examples**: every example validates against its schema.
- **Provider**: run property/fuzz API tests generated from the OpenAPI document against the running component (`schemathesis run`); assert no 5xx, schema-conformant responses, documented status codes only.
- **Consumer / external**: for contracts owned by others, record expected interactions (Pact or WireMock stubs from the verbatim external spec) and assert the adapter never sends undocumented fields or calls.
- **Compatibility**: compare the current spec to the previous version (`oasdiff` or equivalent); breaking change without a major bump is a defect.

## 6. End-to-end tests

- Compose or deploy the minimum full path from the plan's entry event to final state.
- Scenarios: one per final outcome class; unreadable input; ambiguous reference; external outage mid-flow then recovery; duplicate submission; reprocessing after policy change (new version rows, history kept); human-review round trip.
- Assert: final outcome, persisted records and versions, evidence bundle contents + checksum, emitted metrics/events, audit trail, absence of forbidden side effects (no write to systems the guardrails exclude).
- Keep E2E few (about 5-15), stable, and fast; push detail down to component/integration.

## 7. Fault injection and concurrency

Tools: Toxiproxy for network faults, container kill/pause, fake ports that throw, clock skew via injected clock.
Cases: dependency down at start, mid-call, and during commit; worker killed after side effect before ack; duplicate and reordered messages; two workers same key; disk full; memory-heavy file; slow dependency exhausting pool; expired credentials; config flip during processing. Assert: eventual correct state, exactly-once effect, no data loss, alert/log emitted, DLQ contents correct.

## 8. Security tests

AuthN/AuthZ matrix (no token, expired, wrong audience, wrong scope, other tenant) per operation; IDOR on ids; mass assignment; injection (SQL/NoSQL/log/CRLF/path traversal/SSRF) via every free-text and file field; prompt-injection pack (see AI guide); secrets scan (`gitleaks`/`trufflehog`) of repo and of captured logs; dependency audit (`pip-audit`/`npm audit`); IAM/policy review: enumerate granted actions and assert each guardrail (for example no `payment:*`, no write on source buckets); container scan if images are built.

## 9. Performance smoke

Small, repeatable load (`locust`/`k6`/custom) against the local or staging stack: p50/p95 latency, throughput, error rate, queue age, memory, per-unit cost estimate. Report environment, sample size, and the NFR it speaks to. Do not claim an SLO is met from a laptop run; say "no regression and within X of target at N req/s on <env>".

## 10. Flakiness policy

Run suspected flakes 20 times with fixed seed; fix root cause (shared state, sleeps, ordering). Quarantine only with a task ID and an owner, excluded from the pass count and listed in the report.
