# Agent contract (API / MCP proof)

**Principle:** an agent reads the *same* `snapshot.json` the dashboard renders. The agent surface
is `observstory query` today. An MCP server would wrap exactly these five calls
(`prototypes/agent-surface/mcp-tools.json`) and would never crawl GitHub itself.

## Where the snapshot comes from
- In CI: the Action writes `observstory/data/snapshot.json` and sets the output
  `steps.<id>.outputs.snapshot`.
- For an agent working on a checkout: download the latest `observstory-<run_id>` artifact, or
  run `python3 scripts/observstory.py build` locally with `OBSERVSTORY_REPOSITORY` and a token.

## Envelope
Every response has the same shape:

```json
{
  "query": "work_near",
  "args": {"paths": ["src/conversation/store.py", "src/conversation/export.py"]},
  "as_of": "2026-09-22T10:00:00Z",
  "repository": "example/chat-app",
  "answer": { "...": "query-specific" },
  "signals": [ { "id": "overlap:src/conversation", "basis": "derived", "confidence": "high", "evidence": ["..."] } ],
  "evidence_note": "Derived from GitHub metadata ... Observstory describes work, not people."
}
```

## The five questions

| Agent asks | Call | Example response |
|---|---|---|
| What changed since my last run? | `observstory query changes-since 2026-09-21T15:00:00Z` | [`01-changes-since.json`](../../prototypes/agent-surface/examples/01-changes-since.json) |
| Who is active in this subsystem? | `observstory query work-near src/conversation` | [`02-work-near.json`](../../prototypes/agent-surface/examples/02-work-near.json) |
| What overlaps my proposed task? | `observstory query work-near src/conversation/store.py src/conversation/export.py` | [`03-proposed-task.json`](../../prototypes/agent-surface/examples/03-proposed-task.json) |
| What open loops exist? | `observstory query open-loops` | [`04-open-loops.json`](../../prototypes/agent-surface/examples/04-open-loops.json) |
| What is ready for handoff? | `observstory query handoff` | [`05-handoff.json`](../../prototypes/agent-surface/examples/05-handoff.json) |
| What did the team declare, and does the repo agree? | `observstory query coordination` | [`06-coordination.json`](../../prototypes/agent-surface/examples/06-coordination.json) |

"Who is active" is answered as `authors_of_active_work`: the authors of in-flight work items,
so the agent knows who to coordinate with. There is no query that returns what one person has
been doing.

## Suggested agent pre-flight (e.g. in CLAUDE.md or AGENTS.md)

```markdown
Before changing files, run:
  python3 scripts/observstory.py query work-near <files you plan to change> --snapshot <snapshot.json>
If `coordination_needed` is true, list the in-flight work items and their URLs to the user
and ask before proceeding. Treat `heuristic` signals as prompts, not facts.
```

## What MCP does and does not do

| Does | Does not |
|---|---|
| Expose the typed snapshot and five queries to any MCP client | Collect data, receive webhooks or call GitHub |
| Return evidence URLs, basis and confidence | Interpret code, judge designs or summarise with an LLM |
| Share one source of truth with the human dashboard | Keep state of its own |
