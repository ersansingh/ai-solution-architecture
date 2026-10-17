# Runbook: <alert or procedure name>

Owner: <role or TBD (owner)> · Last reviewed: <YYYY-MM-DD> · Rehearsed: <date + evidence | NOT REHEARSED>
Linked alerts: <alert ids> · Linked risks/kill-switches: <R-n> · Requirements/SLOs: <ids>

## Symptoms
What the responder sees (alert text, dashboard panel, user report).

## Impact and severity
Who or what is affected; data-integrity risk yes/no; severity and response time target.

## Quick checks (in order)
1. Dashboard: <link or name>; expected vs abnormal.
2. Command: `<exact command>` -> what a healthy result looks like.
3. Logs/queries: `<query>` filtering by correlation id.
4. Recent changes: last deploys, policy/prompt/model versions, flag changes.

## Mitigation
| Situation | Action | Command / console path | Risk |
| :-- | :-- | :-- | :-- |

Includes the safe degraded mode (for example switch to review-only: `<flag command>`), and what NOT to do.

## Rollback / recovery
Steps to return to the last good state; data compatibility notes; time expected.

## Verification
How to confirm recovery: metrics back within SLO, queue age normal, a synthetic `FAKE` item flows end to end.

## Escalation
Who, when (time boxed), contact method (role names, not personal data).

## After the incident
Record in the decision/incident log; follow-ups as `bd` issues; update this runbook and tests.
