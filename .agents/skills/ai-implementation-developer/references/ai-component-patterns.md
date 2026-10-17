# AI Component Patterns

Apply to every component that calls a model, uses a prompt, scores, extracts, classifies or makes a decision. Model and service choices come from the plan (algorithm report + ADRs); these patterns are how to wrap them.

## 1. Model adapter (one per provider/service)

```text
port:     Extractor.extract(document, schema_version, context) -> ExtractionResult
adapter:  TextractExtractor / BedrockExtractor / FakeExtractor
```

Required behaviour of every real adapter:
- Explicit timeout, bounded retry with jitter on throttling/5xx only, circuit breaker after N consecutive failures, max concurrency.
- Request id, model id/version, prompt version, parameters, input hash, latency, token/page counts and cost estimate recorded on every call (to telemetry, not with content).
- Parses the response into the output schema; schema failure is a typed error, not a partial result.
- Fallback chain from the plan (primary -> alternative -> rules/manual review). The chain is configuration, and which link produced the result is recorded in the output.
- A `Fake` adapter that returns recorded fixtures, so unit tests, CI and the tester never pay for or depend on a live model.

## 2. Prompts, policies and thresholds as versioned data

- Prompts live in `prompts/<name>/<version>.md` (or YAML) with an id, version, owner, intended model, and input/output schema reference. Code references name + version; no inline prompt strings in business logic.
- Business policy (tolerances, thresholds, rounding, allow-lists) lives in `policies/*.yaml` validated by schema, with `policy_version`, `effective_from`, `approved_by`. **Tunable model thresholds** (set by evaluation) are separate from **policy values** (set by the business). Never mix them.
- Unknown or expired version -> fail closed (route to human review), never silently fall back to a default number.

## 3. Output validation and grounding

- Every model output is parsed against a JSON Schema before use.
- Grounding check: each extracted value must be traceable to the source (page + span/box, or a retrieved passage id). Value without source -> `unavailable`/rejected, not accepted.
- Cross-checks that do not use the model: arithmetic (line totals sum to totals), date plausibility, currency consistency, checksum/format patterns (IBAN, VAT, PO number format).
- Confidence is per field; low confidence routes to review. Calibration is the tester's/data team's job; the code only applies the configured threshold.

## 4. Prompt injection and untrusted content

- Document text, retrieved passages and user input go in clearly delimited data sections; the system instruction states they are data, not instructions.
- The model has no tools that can change state unless the plan requires; where tools exist, allow-list them, validate arguments against a schema, and require the policy gate (not the model) to authorise side effects.
- Strip or flag content that looks like instructions in documents; record a security event; never follow it.
- Do not put secrets, other tenants' data or unrelated records into the prompt context.

## 5. Single decision gate

Whenever the plan says "auto-approve only if ...", implement it as **one function** with an explicit allow-list of conditions; anything not matched returns "requires review". Property-test that no combination of inputs outside the allow-list can pass. All other code paths can only escalate, never approve.

## 6. Determinism and reproducibility

- Temperature 0 (or documented seed) for decision-affecting calls; record when a provider cannot guarantee determinism.
- Cache by `(input_hash, model_id, prompt_version, params)`; cache hits are marked in the result.
- Reprocessing the same input with the same versions yields the same decision, or the difference is recorded as new version rows (the plan's versioning rule), never overwritten.

## 7. Human-in-the-loop hooks

- Review tasks carry reason codes, evidence links and the model's suggestion; they time out and escalate per the plan.
- Reviewer decisions are stored as labelled feedback for the evaluation set, with who/when/why.
- A global **review-only mode** flag (kill switch) forces every outcome to human review without redeploying.

## 8. Evaluation hooks (so the tester and data team can measure)

- `evaluate(dataset_manifest) -> metrics.json` entry point per model component, using the same code path as production.
- Metrics named exactly as in the plan's section 7/11 (for example critical-field accuracy, macro-F1, false auto-approve rate).
- Dataset manifests reference documents by id/hash; documents themselves are never committed.

## 9. Cost and rate control

- Per-request and per-day cost budgets in config; exceeding them degrades to the cheaper path or review, and alerts.
- Batch where the provider allows; cap pages per document and tokens per prompt; truncate with a recorded warning, never silently.

## 10. Logging and privacy

- Log ids, hashes, versions, counts, latencies, outcomes. Do not log document content, full prompts or model completions by default; a debug switch that writes them goes to a restricted sink and is off in production.
- Redact PII fields per the plan's privacy section before any telemetry.
- Evidence bundles written once, canonical form, checksum, retention per plan.
