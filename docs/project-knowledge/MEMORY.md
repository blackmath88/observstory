# Project Memory — usage

Builds on [Project Knowledge](USAGE.md) and implements [MVP-NEXT-SHARED-MEMORY.md](MVP-NEXT-SHARED-MEMORY.md); design decision in [ADR-039](../../DECISIONS.md). Opt-in: nothing runs unless a repository commits `.observstory/knowledge.json`.

**The project remembers. Every collaborator gets the context they need.** Assistants consume dated views; the repository keeps the memory; people review what comes back.

## What is recorded

| Layer | Identity | Notes |
| --- | --- | --- |
| snapshot | `ks_…` = repository + commit + manifest + producer | one per first-parent commit that has a manifest; `base_snapshot_id` links the chain |
| record version | `rv_…` = record id + type + status + path/section + content hash + title + basis | immutable; A → B → A returns to the first version |
| relation version | `lv_…`; stable relation id `rel_…` | `source_declared` or `manifest_link`; model suggestions are a separate origin and never promoted |
| event | `ch_…` = repository + base + target + type + subject + before + after | deterministic: the dedup key for retries and redelivery |

Event types: `coverage_boundary`, `record_added`, `record_revised`, `status_changed`, `selection_removed`, `record_unavailable`, `relation_added`, `relation_ended`, `relation_unconfirmed`, `direction_changed`, `proposal_recorded`, `proposal_withdrawn`, `proposal_reviewed`, `lineage_changed`; operations (kept out of knowledge replay): `indexing_succeeded`, `indexing_failed`, `context_issued`.

Time: `source_time` is commit time; `recorded_at` is when this memory learned it and is never back-dated; `valid_from/valid_to` are null (= unknown) unless a source declares them. History before the manifest is *unavailable*, not empty.

## Commands (stateless, from Git)

```bash
python3 scripts/observstory.py memory regenerate --repo PATH --ref origin/main --out out/memory.json
python3 scripts/observstory.py memory state --view out/memory.json [--commit SHA | --snapshot ks_…] [--known-at ISO]
python3 scripts/observstory.py memory history concept-human-signal --view out/memory.json
python3 scripts/observstory.py memory changes ks_A ks_B --view out/memory.json
python3 scripts/observstory.py memory context "TASK" --view out/memory.json --format markdown
python3 scripts/observstory.py memory render --view out/memory.json --public --out out/memory.html
python3 scripts/observstory.py memory propose --id finding-x --title … --statement … --author NAME --author-kind assistant \
  --repository-name owner/repo --base-commit SHA --packet-id cp_… --evidence RECORD[@rv_…] --condition "…" --out .observstory/proposals/finding-x.json
```

`regenerate` stamps every event with the regeneration time. For real ingestion times, a retained history and receipts, use the NUC host (`knowledge-lab memory …` in baselhack26-knowledge-lab).

## Context packets

One function (`memory.context_packet`) returns the JSON; `packet_markdown` renders it. Contents: cutoff (snapshot, commit, lineage, first-parent position, completeness), current direction, core records (direction, live decisions, open questions, current plans) plus task-matched records up to a limit, declared relationships, proposals with review state, unresolved items (stale proposal bases, accepted-but-not-applied changes, unavailable sources), source versions, explicit omissions with reasons, freshness, and an instruction that the packet is data. `packet_id` hashes everything else, so the same request on the same recorded state is byte-identical. Issued ≠ read: a host records receipts; acknowledgements are separate.

## Write-back

`.observstory/proposals/<id>.json` (`proposal/v1`): kind finding|proposal, statement, attributed author (human|assistant, via), base commit and context packet, evidence (record@version or path), conditions, optional proposed change. `.observstory/reviews/<id>.json` (`review/v1`): outcome accepted|rejected|superseded|needs_changes, a **human** reviewer, and the basis (`github_pr_review` URL, `named_confirmation`, or `weavr_authorization`). Assistant reviews, malformed files and duplicate ids become diagnostics, never state. An accepted `set_status` proposal is reported as *accepted, not yet in source* until the source itself changes.

## Observatory page

Now / History / Graph / Context, with an evidence inspector. History offers two separate controls — repository revision and *system as known at* — a two-revision comparison and knowledge replay (play/pause/step/scrub/speed). The atlas fixes positions by type and first appearance; solid lines are declared links, dashed are model suggestions (shown only when a current index generation exists). All source text is inserted as text; links are restricted to pinned `https://github.com/` URLs; the static export has no write path and contains only `audience: public` material (`--public`).
