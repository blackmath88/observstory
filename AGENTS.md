# Agent instructions

## Orientation role

Observstory is the first situational-awareness layer for repositories that use it.

When an assistant enters a repository with Observstory configured:

1. read the current Observstory snapshot / coordination state first;
2. use it to identify relevant work, signals and provenance;
3. inspect repository files directly only as needed to verify or expand the picture;
4. preserve observed / derived / heuristic / declared distinctions;
5. do not turn Observstory signals into orchestration authority.

Boundary:

> **Observatory observes → Weavr decides → runtimes act.**

## If Weavr is present

When the repository is also governed by Weavr:

- Observstory provides repository evidence;
- Weavr owns Project / Mission / Session / Need / Intervention / gate state;
- runtimes execute selected legal actions.

Do not:

- dispatch Missions from Observstory logic;
- route providers from Observstory signals;
- treat an overlap/stale/waiting signal as an automatic stop unless Weavr policy compiles it that way;
- modify the Observstory snapshot to encode Weavr-specific authority.

## If Observstory is absent or stale

Do not block useful work.

Fall back to direct repository inspection and make the evidence limitation explicit.

## Canonical integration

Read `docs/integrations/weavr.md` for the producer/consumer boundary with Weavr.
