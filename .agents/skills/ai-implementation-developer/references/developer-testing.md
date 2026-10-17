# Developer-Owned Tests (unit level)

Scope: the developer writes **unit tests** for the code they write, in `tests/unit/`, in the same change. Component, integration, contract, E2E, golden-set evaluation, fault injection, security and performance suites belong to `ai-implementation-tester`. Make them possible; do not write them.

## What a good unit test here looks like

- Tests behaviour through the public function/class, not private details.
- Hermetic: no network, no clock, no randomness, no filesystem outside a temp dir. Time and ids are injected.
- Table-driven for rule logic (input, expected, requirement ID in the case name).
- Includes boundary values (just inside / on / just outside every tolerance), empty and maximal inputs, and the negative path for every guardrail.
- Fast: the whole unit suite runs in well under a minute.
- Names say what and why: `test_BR07_price_diff_on_tolerance_boundary_is_accepted`.
- Tag with the requirement: marker `@pytest.mark.req("BR-07")` (or a docstring `Req: BR-07`) so `plan_extract.py trace` finds it.

## Property tests (Hypothesis or equivalent) where the plan states an invariant

| Invariant | Example property |
| :--- | :--- |
| Money never loses or gains value | sum of allocated parts equals the whole for any split |
| Idempotent replay | `apply(apply(x)) == apply(x)` and result key is stable |
| Order independence | shuffled line order gives the same decision |
| Gate safety | no input outside the allow-list returns "auto-approve" |
| Monotonic tolerance | widening a tolerance never turns an accepted case into a rejected one |
| Round trip | `parse(serialize(x)) == x` for contracts |

## Mocks, fakes and fixtures

- Fake at **ports** (storage, queue, model, PO source, API client) using the in-repo fake adapters; do not patch internals.
- Fixtures are synthetic and labelled `FAKE`; a seed script generates them deterministically from a seed. No real documents, names, bank details or credentials.
- Recorded model responses for adapter parsing tests are hand-written minimal examples, including malformed ones.

## Coverage

Follow the thresholds in `engineering-profile.md` or the plan (typical: >= 80% on core modules, 100% branch on gate and money code). Coverage is a smoke alarm, not a goal: a line executed without an assertion does not count. State actual numbers from a run.

## Handing over to the tester

Provide in the hand-off: how to run each unit command, how to build the fakes, the list of ports with fake adapters, the seed generator command, and the **known untested areas** (so the tester targets them rather than rediscovering them).
