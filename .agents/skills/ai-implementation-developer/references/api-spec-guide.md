# API Specs and Data Contracts (contract-first)

Source: plan section 8 (Interfaces and Contracts), section 6 (In -> out per component), design document flows.

## Which spec for which interface

| Interface kind | Spec | File |
| :--- | :--- | :--- |
| HTTP/REST this system exposes | OpenAPI 3.1 | `api/openapi.yaml` |
| HTTP/REST owned by someone else (existing backend, PO system) | Copy the approved spec verbatim; never edit | `api/external/<name>.yaml` |
| Queue / topic / event / webhook | AsyncAPI 3.0 | `api/asyncapi.yaml` |
| Payloads, stored documents, evidence bundles, policies, model outputs | JSON Schema 2020-12 | `schemas/<name>.schema.json` |
| gRPC (only if plan says so) | `.proto` | `api/proto/` |

If the plan marks a contract **TBD** (open decision), write the spec for what this system needs, mark it `x-status: proposed`, and list it in the hand-off as needing approval. If an existing contract lacks a needed capability, document the gap in `docs/contract-gaps.md` and build to the existing contract.

## OpenAPI rules

- `info.version` follows semver; breaking changes bump major and a new path prefix (`/v2`).
- Every operation has `operationId`, summary, tags, request/response schemas via `$ref` to `components/schemas`, and **all** error responses.
- One error shape for the whole API (RFC 9457 `application/problem+json` is a good default): `type`, `title`, `status`, `detail`, `code` (stable machine code), `retryable` (bool), `correlation_id`.
- Idempotency: mutating POST/PUT take an `Idempotency-Key` header; the spec states replay behaviour (same key + same body -> same response; same key + different body -> 409/422).
- Pagination: cursor-based (`next_cursor`, `limit` max stated); list order is deterministic.
- Security schemes declared (`bearer` JWT / OAuth2 client credentials / mTLS per plan); every operation lists required scopes. No operation is unauthenticated unless the plan says so (health probes excepted).
- Money: object `{ "amount": "123.45", "currency": "EUR" }` with amount as a **string** decimal or integer minor units, never a JSON float. Dates RFC 3339 UTC.
- Enumerations for decision outcomes are closed lists copied from the plan; there is no outcome the plan forbids (for example no `fraud` value if the plan says no fraud determination).
- Include `examples` for success and the main errors; the tester uses them as contract fixtures.
- Rate limits and payload size limits stated in `x-` extensions and in the description.

## AsyncAPI rules

- One channel per queue/topic; message has `schema_version`, `event_id`, `occurred_at`, `correlation_id`, `idempotency_key`, payload `$ref`.
- State delivery semantics (at-least-once assumed), ordering guarantees (usually none), DLQ channel and max receive count, visibility timeout, retry/backoff.
- Consumers must be idempotent: document the dedupe key.

## JSON Schema rules

- `$schema`, `$id`, `title`, `schema_version` const or required property, `additionalProperties: false` on objects you own.
- Missing data is explicit: `{ "status": "unavailable", "reason": "not_present|illegible|ambiguous" }` rather than null or empty string, if the plan has such a rule.
- Model outputs carry `value`, `confidence` (0-1), `source` (page, bounding box or text span) and `status`; a schema-level rule (`if/then`) requires `source` whenever `value` is present, so ungrounded values cannot validate.
- Policy files (tolerances, thresholds, rounding): schema requires `policy_version`, `effective_from`, `approved_by` fields; unknown version at runtime fails closed.

## Generating and keeping specs honest

1. Write the spec first; generate typed models from it when the stack supports it (for example `datamodel-code-generator` for Pydantic, `openapi-typescript`), or write models and add a test that the OpenAPI/JSON Schema matches them. A spec that drifts from code is a defect.
2. Validate: `spectral lint api/openapi.yaml`, `openapi-spec-validator`, `ajv`/`jsonschema` against examples. Record RAN or READ.
3. Add `docs/contract-changelog.md`; each change states compatible/breaking.
4. Hand the tester the spec paths and the examples; they derive contract tests from them without reading the code.

## Minimal checklist

- [ ] Every plan section 8 row has a spec or an explicit "external, copied" or "TBD, proposed" entry
- [ ] Error model identical across operations
- [ ] Idempotency and pagination defined where relevant
- [ ] Auth scopes on every operation
- [ ] No floats for money; no forbidden enum values
- [ ] Examples present and validate against their schemas
