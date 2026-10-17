# Engineering Implementation Plan: <System name>

> **Problem statement:** [`<file>`](<relative path>)
> **Algorithm / model recommendation:** [`<file>`](<relative path>)
> **System design:** [`<file>`](<relative path>) · **Diagram:** [`<file>.drawio`](<relative path>) (<N> pages)
> **Strategy / funding roadmap:** [`<file>`](<relative path>) or "none"
> **Plan date / version:** <YYYY-MM-DD> · v<n> (draft for review)
> **Status labels used:** **VERIFIED** (I ran or parsed it) · **INFERRED** (read from the documents) · **ASSUMPTION** (needs confirmation)

---

## 1. Purpose and Scope

One paragraph on what this plan delivers.

**In scope** (bullets, taken from the problem statement)
**Out of scope / guardrails** (bullets; each is a rule the build must enforce, for example "no payment permissions in any IAM role")
**Team and constraints:** team size, roles, deadline, budget, forbidden tools. `ASSUMPTION` if unknown.

---

## 2. Inputs and Inventory

| Input | Path | Version/date | Notes |
| :--- | :--- | :--- | :--- |

**Diagram inventory summary** (from `scripts/drawio_inventory.py`, VERIFIED)

| Page | View | Components | Edges | Script issues |
| :--- | :--- | :-: | :-: | :--- |

Limits: the script reads structure, not visual layout. State whether a human visual check was done.

---

## 3. Requirement-to-Design Traceability

| Req ID | Requirement (short) | Source § | Design component(s) | Diagram page | Model / rule | Milestone | Test ID(s) | Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

Coverage = Full / Partial / **Gap**. Add a second table: **diagram components with no requirement** (justify or flag).

---

## 4. Gaps, Conflicts and Corrections to the Inputs

| ID | Sev | Source | Finding (quote both sides) | Resolution / who approves | Milestone |
| :--- | :-: | :--- | :--- | :--- | :--- |

Group as 4.1 Requirements ↔ design, 4.2 Model report ↔ design, 4.3 Design ↔ diagram, 4.4 Design ↔ IaC/pipeline. List **required edits to input documents** separately; the plan does not edit them.

---

## 5. Decisions

### 5.1 Architecture decisions (ADR)
| ID | Decision | Options considered | Why | Consequence |
| :--- | :--- | :--- | :--- | :--- |

### 5.2 Open decisions (OD)
| ID | Decision needed | Owner | Default if no answer | Needed by (milestone) | Blocks |
| :--- | :--- | :--- | :--- | :--- | :--- |

---

## 6. Component Build Specs

One row per buildable component (group by diagram container). Link each to its diagram page.

| Component | Purpose | Tech / service | Inputs → outputs | Data stores | Key behaviours & edge cases | Owner role | Size (S/M/L) | Acceptance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :-: | :--- |

---

## 7. Data and Model Plan

- **Data sources and access:** source, owner, access method, sample size needed, gate to confirm.
- **Data contracts:** schemas, required fields, how "unavailable" is represented, versioning.
- **Golden / evaluation set:** size, labelling process and labeller, split strategy, freeze date, storage.
- **Models and rules:** primary, alternative, baseline (from the algorithm report), thresholds to be tuned vs policy values owned by the business.
- **Training / prompts / policies:** how versions are stored, promoted and rolled back.
- **Metrics and targets:** metric, target, measured on, gate where it applies.

---

## 8. Interfaces and Contracts

| Interface | Producer → consumer | Protocol / schema | Versioning & compatibility | Error semantics | Test |
| :--- | :--- | :--- | :--- | :--- | :--- |

Include the existing API contract and any capability gaps that need approval.

---

## 9. Repository Layout and Engineering Standards

```text
<proposed tree>
```

Language/runtime, lint/type/test commands, branching, code review rules, secret handling, link to the project `engineering-profile.md` (or "to be created from the developer-engineering template").

---

## 10. Milestone Plan

For each milestone M0...Mn:

**Mn - <name>** · Goal · Gate/funding link · Estimate (range, basis) · Depends on

| Task ID | Task | Owner role | Depends on | Estimate | Req / ADR / page | Done when |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

**Exit criteria** (measurable): ...
**Continue / stop rule:** ...

Summary timeline table at the end: milestone, effort range, calendar range (only if team size known), critical path.

---

## 11. Test and Verification Strategy

| Test ID | Level | What it proves | Req IDs | Data / environment | Pass threshold | Gate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

Levels: unit, property, golden-set/model evaluation, contract, integration, fault injection, security & AI safety, performance & cost, shadow acceptance. State what runs in CI vs nightly vs manually.

---

## 12. Environments, IaC, CI/CD and Release

- **Environments:** table of dev/staging/prod/DR and how they differ.
- **IaC status:** what the infrastructure page needs vs what exists (VERIFIED/INFERRED), missing resources, state backend.
- **CI/CD:** required checks, promotion rules, approvals, what does not exist yet.
- **Release & rollback:** flags, canary, review-only mode, rollback rehearsal, data migration/reprocessing rules.
- **Run readiness:** dashboards, alerts ↔ SLOs, runbooks, on-call, backup/restore test.

---

## 13. Non-Functional Plan

| NFR | Target (source or `TBD`) | How it is built | How it is measured | Milestone |
| :--- | :--- | :--- | :--- | :--- |

Cover: security and access, privacy/PII, audit and retention, availability and DR, latency and throughput, observability, cost/FinOps, idempotency and retries, compliance mapping.

---

## 14. Risks and Kill-Switches

| ID | Risk | Likelihood | Impact | Early signal | Mitigation | Owner | Retired at |
| :--- | :--- | :-: | :-: | :--- | :--- | :--- | :--- |

Then the **kill / pivot rules** for the top risks (threshold, evidence, decision owner, fallback).

---

## 15. Definition of Done and Hand-off

**Definition of done:** (per task and per milestone).

| Role | Starts with | Reads first | Deliverable | Done when |
| :--- | :--- | :--- | :--- | :--- |
| developer | | | | |
| tester | | | | |
| devops-engineer | | | | |
| data / AI | | | | |
| business owners | | | | |

---

## 16. Backlog

Items deliberately deferred, with reason and trigger to revisit.

---

## Appendix A. Diagram Inventory (full)

Paste the script output, or link to the saved file.

## Appendix B. Assumptions Register

| ID | Assumption | Source | Impact if wrong | Confirm by |
| :--- | :--- | :--- | :--- | :--- |

---

## Plan quality checklist (tick before reporting)

- [ ] Every requirement has a row in section 3 and at least one test ID
- [ ] Every diagram component is traced to a requirement or flagged
- [ ] Gap table quotes both sides of each conflict, with severity and owner
- [ ] Out-of-scope rules appear as enforceable guardrails and have tests
- [ ] Each milestone has measurable exit criteria and a continue/stop rule
- [ ] Riskiest assumptions are tested in the earliest milestones
- [ ] Estimates are ranges with a basis; no calendar dates without a team size
- [ ] Placeholders and unknown numbers are marked ASSUMPTION/TBD with an owner
- [ ] Verified vs inferred vs assumed statements are labelled honestly
- [ ] Hand-off table is complete; no commits, pushes or issue creation without being asked
