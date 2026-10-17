# Input Reconciliation Checklist

Run every check. Each failure becomes a row in the plan's gap table (section 4). Severity: **H** = the build would be wrong or a requirement unmet; **M** = works but fragile, costly or ambiguous; **L** = hygiene.

## A. Problem statement vs design

| # | Check | Typical severity |
| :-: | :--- | :-: |
| A1 | Every requirement / acceptance criterion has at least one named component in the design **and** the diagram | H |
| A2 | Every out-of-scope item stays out: no component, IAM permission, API or data flow implements it (for example payments, ledger posting, frontend) | H |
| A3 | "Must not" rules are enforced by a mechanism, not a sentence (a gate, a permission boundary, a test) | H |
| A4 | Stated numbers agree (volume, latency, availability, retention, accuracy targets) or are explicitly `TBD` with an owner | M |
| A5 | Terms and status models match (outcome names, document types, roles) | L |
| A6 | Compliance obligations (audit trail, retention, privacy) have a component and a test | H |
| A7 | Open business decisions in the problem statement are listed as decisions with owner and a milestone deadline | H |

## B. Algorithm report vs design vs diagram

| # | Check | Typical severity |
| :-: | :--- | :-: |
| B1 | The top-ranked model/approach from the report appears in the design and on a diagram page | H |
| B2 | Fallback and baseline models in the report have a place (fallback chain, benchmark harness) | M |
| B3 | Metrics and targets in the report are the ones the test strategy and gates will use | H |
| B4 | Data assumptions (volume, labels, imbalance, golden set) have a data-acquisition task | H |
| B5 | Training / fine-tuning, registry, serving and monitoring in the report exist as components | M |
| B6 | The report's "ML decides vs rules decide" boundary is respected in the design flow | H |
| B7 | Accuracy / latency figures that are estimates are labelled as such and scheduled for measurement | M |

## C. Design document vs Draw.io file

| # | Check | Typical severity |
| :-: | :--- | :-: |
| C1 | Every component named in the design text exists in the inventory (match by meaning, not exact string) | M |
| C2 | Every diagram component is described or justified in the design | L |
| C3 | Flows in the design's "interaction flow" exist as labelled edges on the logical page | M |
| C4 | Components with **no connection** (script output) are intentional, or flows are missing | M |
| C5 | Diagram pages cover the views the design claims (logical, infra, security, observability, CI/CD, lineage, resilience, orchestration, FinOps, governance) | L |
| C6 | Region / AZ / network details match the infrastructure text | M |
| C7 | Page and cell issues from the script (unlabeled edges, low density, duplicate labels) are noted for a diagram fix | L |

## D. Design vs IaC / pipeline files (if present)

| # | Check | Typical severity |
| :-: | :--- | :-: |
| D1 | Each infrastructure component on the infra page has a Terraform resource, or is on a "not yet in IaC" list | M |
| D2 | IAM policies are least-privilege and exclude forbidden capabilities | H |
| D3 | Placeholders (image, budget, retention, SLO thresholds) are tracked as open decisions | M |
| D4 | The pipeline's test paths, scripts and flags exist or are scheduled tasks | M |
| D5 | State backend, environments and promotion path are defined | M |
| D6 | Nothing claims to be validated unless it was run | H |

## E. Cross-cutting

| # | Check | Typical severity |
| :-: | :--- | :-: |
| E1 | Idempotency, retries, DLQ, timeouts exist for every external call and queue | H |
| E2 | PII / secrets never reach logs, prompts or telemetry | H |
| E3 | Every AI output that can affect money, safety or compliance has a human or rule gate | H |
| E4 | Cost control exists for any metered model/API (cache, cap, fallback) | M |
| E5 | Evaluation data is separated from training data (supplier/time/group split) | H |
| E6 | The plan's kill-switch / rollback path is real (feature flag, review-only mode, previous version) | H |
| E7 | Ownership: every component has an owning role and an on-call path | M |

## How to write a finding

`ID | Sev | Source (doc §/page) | Finding (what disagrees, with the two quotes or values) | Resolution (what the plan does, who approves) | Milestone`

Quote both sides of a conflict. Do not write "inconsistent" without showing where.
