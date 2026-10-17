# CI/CD Pipeline Stages and Gates

Platform default: GitHub Actions. Translate 1:1 for other platforms. All stages call the project's `make` targets.

## Pipeline map

| # | Stage | Runs on | Blocks merge | Command (from hand-off) | Notes |
| :-: | :--- | :--- | :-: | :--- | :--- |
| 1 | Setup | every push/PR | - | `make install` | Cache by lock-file hash; pinned runtime |
| 2 | Lint + format check | every push/PR | Yes | `make lint` | |
| 3 | Type-check | every push/PR | Yes | `make typecheck` | |
| 4 | Unit tests + coverage | every push/PR | Yes | `make test-unit` | Coverage thresholds from profile/plan; upload report |
| 5 | Contract tests | PR (path: `api/`, `schemas/`, `src/`) | Yes | `make test-contract` | Spec lint, example validation, breaking-change diff vs base branch |
| 6 | Component tests | PR | Yes | `make test-component` | |
| 7 | Integration tests | PR (service containers) | Yes | `make test-integration` | Compose/Testcontainers; time-boxed |
| 8 | Security | every push/PR | Yes (High+) | gitleaks, pip-audit/npm audit, Semgrep/CodeQL, Dockerfile lint | SARIF upload; allow-list file reviewed |
| 9 | IaC validate + scan | PR (path: `terraform/`) | Yes | `terraform fmt -check`, `validate`, `tflint`, `checkov`/`trivy config` | Plan output as PR comment/artifact when credentials exist |
| 10 | Build image | PR + main | Yes | `docker build` (or buildx) | Non-root, pinned digest, SBOM (syft), scan (trivy), tag by SHA |
| 11 | AI evaluation gate | PR touching models/prompts/policies; nightly | Yes where plan says (G1+) | `make test-eval` | Compare metrics with baseline file; fail on regression beyond plan tolerance; cost-capped, recorded model by default |
| 12 | E2E | main + nightly | Gate to promote | `make test-e2e` | Against composed stack or dev environment |
| 13 | Publish artifact | main | - | push image/package to registry | Immutable tag = commit SHA; provenance attestation |
| 14 | Deploy dev | main | - | IaC apply / service update via OIDC | Only after the user enables deploy jobs |
| 15 | Smoke + promote staging | after dev | Approval | smoke tests, then staging deploy | Environment protection rules |
| 16 | Shadow / canary | staging -> prod | Approval | per plan release strategy | Review-only mode first if plan says |
| 17 | Prod deploy | after approval | Approval + change record | same artifact as staging | Rollback step and auto-rollback trigger |

Deploy jobs (14-17) are written but **disabled by default** (`if: vars.ENABLE_DEPLOY == 'true'`) until the user enables them.

## Workflow design rules (GitHub Actions)

- `permissions:` at workflow level set to `contents: read`; raise per job only as needed (`id-token: write` only for OIDC jobs, `security-events: write` only for SARIF upload).
- Pin third-party actions to full commit SHA with a comment of the version; Dependabot/Renovate config for updates.
- `concurrency:` group per ref with `cancel-in-progress: true` for CI; `false` for deploy.
- `timeout-minutes` on every job; `fail-fast: false` only for matrices where all results matter.
- Cache: dependency cache keyed on lock file; never cache secrets or credentials.
- `pull_request` (not `pull_request_target`) for untrusted code; no secrets exposed to fork PRs.
- Use `environment:` for staging/prod to get protection rules and scoped secrets/variables.
- OIDC: `aws-actions/configure-aws-credentials` with `role-to-assume` and session duration minimal; trust policy limited to repo, branch/environment.
- Do not echo secrets; no secrets in command lines; mask derived values (`::add-mask::`).
- Step summaries (`$GITHUB_STEP_SUMMARY`) show test counts, coverage, eval metrics, image digest.
- Scheduled workflows (nightly eval/E2E) tolerate delays and use idempotent runs; alert on failure.
- Matrix kept minimal; one supported runtime version unless the plan says otherwise.
- Reusable workflows (`workflow_call`) for repeated blocks if more than one service.

## Gates and branch protection (document; do not apply unasked)

Required checks: lint, typecheck, unit, contract, component, integration, security, iac, build. One approving review, CODEOWNERS for `api/`, `policies/`, `terraform/`, `.github/`. Linear history optional per profile. Policy files and prompts need an approver from the business owner group (CODEOWNERS), since they change decisions.

## Model, prompt and policy promotion

- Artifacts (model version, prompt version, policy YAML) are versioned files or registry entries; promotion = a PR changing a pointer, with the evaluation report attached.
- Gate: metrics >= plan thresholds and not worse than baseline beyond tolerance; zero adversarial violations; cost per unit within budget.
- Rollback = revert pointer (one commit or one flag), tested in staging.

## Pipeline testing

`actionlint` on workflows; dry-run the scripts the workflow calls; run the same `make` targets locally; for deploy jobs use a throw-away non-production environment only with the user's consent.
