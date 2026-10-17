# Edge Cases and Production-Readiness Self-Check

Apply at every boundary you write. Add domain cases from the plan's "key behaviours & edge cases" column.

## Boundary catalogue

| Area | Cases to design for |
| :--- | :--- |
| Input | empty, null, missing field, extra field, wrong type, huge payload, unicode/RTL/emoji, control characters, duplicate keys, malformed encoding, zero-byte file, password-protected or corrupt file, wrong MIME vs extension, zip bombs / page-count bombs |
| Numbers and money | negative, zero, very large, rounding at boundaries, currency mismatch, multiple currencies, tax-inclusive vs exclusive, per-line vs per-total rounding, locale separators (1.234,56 vs 1,234.56), minor-unit differences (JPY) |
| Dates and time | timezone, DST, leap day, end of month, future dates, date before epoch, ambiguous formats (03/04/2026), clock skew between systems |
| Identity and keys | duplicates, near-duplicates, same id different content, id reuse, case/whitespace/hyphen variants, leading zeros |
| External calls | timeout, slow response, throttling (429), 5xx, partial response, wrong schema, auth expiry mid-run, DNS failure, response that is valid but wrong |
| Messaging | at-least-once duplicates, out-of-order, poison message, visibility timeout shorter than processing time, DLQ overflow, redrive storms |
| State and data stores | concurrent writers, lost update, partial write, crash between steps, unique-key conflict, schema migration mid-flight, read-your-writes lag |
| Idempotency and retries | replay same event, replay with changed content, retry after success whose ack was lost, retry storms (backoff + jitter + budget) |
| Files and storage | name collisions, path traversal, very long names, concurrent upload of same object, object overwritten or deleted after listing |
| AI / model | empty or refusal output, truncated output, invalid JSON, hallucinated value, injection text, language mismatch, low-quality scan, provider model deprecation, latency spike, cost spike |
| Security | missing/forged/expired token, wrong scope or tenant, IDOR, mass assignment, SSRF through user-supplied URL, log injection, secrets in errors |
| Resources | memory growth on large files, file-descriptor leaks, unbounded queues/caches, thread/connection pool exhaustion, cold starts |
| Operations | config missing/invalid at start, partial deployment (old and new versions together), rollback with new data, feature flag flip mid-request |

## Patterns to use

- **Validate at the edge, trust inside**: parse into typed objects once; core code takes only valid types.
- **Fail closed** on policy/permission/config doubt; **fail soft** (degrade) on optional enrichment.
- **Timeouts everywhere** with an overall deadline passed down; no unbounded waits.
- **Retries**: bounded attempts, exponential backoff with jitter, only for retryable errors, with a retry budget; non-idempotent operations need an idempotency key.
- **Idempotent writes**: natural key or content hash, upsert/conditional put, "processed" marker written in the same transaction as the effect.
- **Atomic multi-step changes**: transaction, outbox, or write-new-then-switch pointer; never half-applied state visible.
- **Bulkheads**: separate pools/queues for slow dependencies; one bad tenant/document cannot starve others.
- **Poison handling**: after N failures move to DLQ with reason and original payload; alert; replay tool exists.
- **Time and randomness injected**: clock and id generator are parameters so tests are deterministic.
- **Explicit enums** for outcomes; `match` on them exhaustively; unknown value -> error, not default branch.

## Production-readiness self-check (before hand-off)

Mark each Yes / N/A (reason) / No (listed as a defect or stub).

- [ ] Every external call has timeout, bounded retry, and idempotency or "safe to repeat" reasoning
- [ ] Every input boundary validates against a schema; invalid input yields a typed error and a safe outcome
- [ ] No float for money; rounding mode and currency handled explicitly
- [ ] Replaying any event/message twice produces one effect
- [ ] Crash at any step leaves consistent state; restart resumes safely
- [ ] Concurrency: two workers on the same item cannot both succeed incorrectly
- [ ] Guardrails from the plan have an enforcement point and a unit test
- [ ] Model outputs are schema-validated and grounded; fallback chain exists and is configurable
- [ ] Auto-decision gate is a single function with an allow-list
- [ ] Logs are structured, carry a correlation id, and contain no secrets, PII or document content
- [ ] Metrics exist for throughput, latency, errors, queue age, decisions by outcome, model cost
- [ ] Config is validated at start; secrets come from the secret manager at runtime
- [ ] Health/readiness reflect dependencies appropriately (liveness does not call dependencies)
- [ ] Resource limits (payload size, page count, concurrency, memory) are enforced and tested
- [ ] README commands work from a clean checkout; all hand-off commands were RAN
- [ ] No dead code, no unlinked TODOs, no commented-out blocks, no wildcard excepts
