# Project Scaffold (framework template)

Use the language and layout from the plan (ADRs, section 9). The defaults below are for a Python service, which is the most common choice for AI systems; translate for other stacks (TypeScript/Java/Go) keeping the same structure of concerns.

## Layout

```text
<repo or implementation>/
  README.md  engineering-profile.md  Makefile  pyproject.toml  .env.example  .gitignore  Dockerfile
  api/            openapi.yaml  asyncapi.yaml  external/
  schemas/        *.schema.json
  policies/       *.yaml            # versioned business policy; sample values clearly marked FAKE
  src/<package>/
    common/       config.py  errors.py  ids.py  money.py  time.py  logging.py  telemetry.py  retry.py
    <component>/  one package per plan component, in flow order
    ports/        interfaces for every external system (storage, queue, model, PO source, API)
    adapters/     real and fake implementations of the ports
    app/          composition root: wiring, entry points (handlers, CLI, API server)
  tests/          unit/ (developer)  component/ integration/ contract/ e2e/ eval/ fault/ security/ perf/ (tester)
  scripts/        seed data generator, local run helpers
  docs/           components/  adr/  runbooks/
```

Ports and adapters isolate every external dependency so unit tests need no network and the tester can swap fakes or containers.

## Tooling defaults (Python)

| Concern | Default | Note |
| :--- | :--- | :--- |
| Packaging | `pyproject.toml`, `src/` layout, pinned lower and upper bounds, lock file (`uv.lock` or `pip-compile`) | Reproducible installs |
| Lint / format | `ruff check`, `ruff format` | Rules from profile |
| Types | `mypy --strict` on core and money/rules modules, normal elsewhere | Pydantic v2 for schemas |
| Tests | `pytest`, `pytest-cov`, `hypothesis` for properties | Markers: `req`, `unit`, `component`, `integration`, `e2e` |
| Config | `pydantic-settings`, env-driven, validated at startup, fail fast | No secret defaults |
| Logging | JSON logs, correlation id in every line, redaction filter for PII and secrets | Never log document content or full prompts by default |
| HTTP | `httpx` with explicit timeouts; `tenacity`-style bounded retry with jitter | Retries only for idempotent calls or with idempotency keys |
| API server | FastAPI (OpenAPI generated and **diffed** against `api/openapi.yaml`) | Only if the plan exposes HTTP |
| Workers | Handler functions with a thin adapter for Lambda/ECS/Functions; no framework in the core | Keeps cloud choice swappable |
| Container | Multi-stage, non-root user, pinned base image digest, no build secrets | Image scan in CI |
| Task runner | `Makefile` (or `justfile`) targets: `install lint typecheck test test-unit run seed clean` | CI calls the same targets |

## Cross-cutting modules every project gets

- `errors.py`: base `AppError(code, message, retryable, details)`; subclasses for validation, not-found, conflict, upstream, policy. Maps to API problem+json.
- `config.py`: one `Settings` class; `Settings()` raises with a clear list of missing/invalid variables; separate settings for secrets (read from a secret manager at runtime).
- `retry.py`: `retry(policy)` with attempts, base delay, max delay, jitter, retryable-exception predicate, deadline propagation.
- `telemetry.py`: tracing span helper, counters/histograms (`requests_total`, `latency_seconds`, `model_cost_usd`, `decision_total{outcome}`), no PII in labels.
- `ids.py`: deterministic ids from content hash for idempotency (`sha256(canonical_json(...))`); ULID/UUIDv7 for events.
- `money.py` (if money is involved): `Money(amount_minor:int, currency:str)`, rounding mode from policy, no floats, conversion only with an explicit rate object.
- `policy/` loader (if policy-driven): loads YAML, validates against schema, exposes `policy_version`, fails closed on unknown or expired policy.

## README must contain

1. What this is (two sentences) and the plan it implements.
2. Prerequisites and exact install command.
3. Run locally with fakes (no cloud account needed).
4. Run each test level (`make test-unit`, others as tester adds them).
5. Config reference (variable, meaning, default, secret yes/no).
6. Folder map and where to add a new component.
7. Known limits and stubs (link to hand-off).

## Scaffold done when

`make install lint typecheck test-unit` runs from a clean checkout (RAN, output recorded), the service starts locally against fakes, and `/health` or equivalent entry responds.
