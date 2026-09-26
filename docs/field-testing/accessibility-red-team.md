# Field test: Accessibility Red Team

Repository:

https://github.com/blackmath88/accessibility-red-team

Tracking issue:

https://github.com/blackmath88/observstory/issues/13

## Integration

The project configured six semantic lanes:

```text
Intent & Governance
Scout & Capture
Probe & Journey
Evidence & Report
Validate & Learn
Automation
```

It also uses declared coordination for architecture decisions and the next validation commitments.

The Observstory artifact remains private-to-repository readers through GitHub Actions artifacts; Pages is intentionally deferred during framework evaluation.

## First run

Run:

https://github.com/blackmath88/accessibility-red-team/actions/runs/36235833257

Observed:

```text
in_flight       0
active areas    23
commits/window  100
overlap         0
stale           0
waiting         0
burst           1
degraded        0
API calls       105
```

The burst signal correctly captured a rapid direct-to-main agent-assisted build stream.

## What the field test found

### Strong

- low-friction Action integration;
- typed snapshot is useful before looking at the UI;
- custom lanes produce a meaningful architecture map;
- declared + observed coordination adds context without task-board upkeep;
- concurrency cancellation behaves well during rapid pushes;
- evidence and rule provenance remain inspectable.

### Friction

1. A very active direct-to-main build can show `summary.in_flight = 0` while the map is full of recent direct work.
2. Custom semantic lanes benefit from clearer explanation of why an area falls into `Other`.
3. Long-running projects sometimes want a declared current focus without inventing a due date.
4. Bootstrap commitments linked to recently changed paths can reconcile as already landed.
5. A high `max_commits` setting makes API-call cost visible; users could benefit from budget guidance.

## Slow field-eval loop

Accessibility Red Team added a consumer-owned evaluator:

```text
fresh snapshot
→ explicit expectations
→ eval.json + report.md
→ candidate feedback
```

Initial checks include:

- snapshot contract;
- expected lane presence;
- fallback-area count;
- degraded collection;
- API budget;
- coordination presence;
- evidence/rule contract;
- summary consistency;
- direct-to-main activity semantics;
- bootstrap coordination behavior.

Cadence:

- manual;
- weekly.

This intentionally does not run hourly or on every push.

## Framework lesson

A useful separation is emerging:

```text
Observstory core
facts → typed project state → evidence-backed signals

Consumer field eval
typed project state → project-specific expectations → improvement candidates
```

The second layer can improve the framework without turning the framework into a self-modifying system.
