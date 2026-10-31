# Project Knowledge — usage (opt-in slice)

Implements the deterministic part of the [concept](https://github.com/blackmath88/observstory/blob/1823a9bf54025a0200802bef776c7a0472baaf46/docs/project-knowledge/CONCEPT-AND-BUILD-PLAN.md) and [sparring findings](https://github.com/blackmath88/observstory/blob/1823a9bf54025a0200802bef776c7a0472baaf46/docs/project-knowledge/PERPLEXITY-SPARRING.md) (branch docs/project-knowledge-concept) as an adjacent module. `observstory.snapshot/v1`, the metadata-only collector and the default dashboard are unchanged; nothing runs unless a repository commits a manifest **and** the caller asks for it.

## Manifest (owned by the source repository)

`.observstory/knowledge.json`, schema `observstory.knowledge-manifest/v1`: explicit `records` (id, type, path, optional `section` heading, status, optional `declared_in` quotes), explicit `links`, and `imports` (currently `observstory.coordination/v1`, which brings in existing decisions and open questions with their own IDs and statuses). Ordinary Markdown needs no front matter. Example: [baselhack26-open-presence](https://github.com/blackmath88/baselhack26-open-presence/blob/main/.observstory/knowledge.json).

| type | statuses |
| --- | --- |
| concept | current, candidate, superseded, historical |
| decision | stated, proposed, declared (import only — a manifest cannot approve), superseded |
| research | reference, input, historical |
| plan | current, historical |
| question | open, resolved |
| module | optional, current, historical |

Relations: supersedes, informs, qualifies, applies_to, plans, answers.

## Producer rules

- Resolves the ref **once**; reads the manifest and every selected file as Git objects of that commit (never the working tree or a remote).
- `declared_in` quotes are checked verbatim (whitespace-normalised) at that commit; found → basis `source_declared`, else `manifest_classification` plus a warning.
- Current direction = exactly one `concept` with status `current` and a verified source declaration. Otherwise `unresolved` with a reason. Never chosen by date or order.
- Identity: `logical_id` (repo#id) ≠ content (`blob`, `content_sha256`) ≠ membership (`snapshot_id` = repo + commit + manifest + producer version).
- A missing/unreadable source makes the artifact `complete: false`; it is never reported as a removal.
- Diagnostics: duplicate_id, dangling_link, supersession_cycle, superseded_but_current, invalid_status, confirmation_required, declaration_not_found, section_not_found, source_missing_at_commit …
- The producer does not fetch. `upstream_check` says so; a fresh `generated_at` is not evidence of a fresh ref.

## Commands

```bash
python3 scripts/observstory.py knowledge build --repo PATH --ref main --out out/data/knowledge.json --html out/knowledge.html [--base-ref REF | --base OLD.json]
python3 scripts/observstory.py knowledge brief --artifact out/data/knowledge.json --format text
python3 scripts/observstory.py knowledge record concept-human-signal --artifact out/data/knowledge.json
python3 scripts/observstory.py knowledge changes --base old.json --target new.json
python3 scripts/observstory.py knowledge changes --repo PATH --base-ref REF_A --ref REF_B
python3 scripts/observstory.py knowledge render --artifact out/data/knowledge.json --changes out/data/knowledge.changes.json --out out/knowledge.html
```

All JSON answers carry `snapshot` (repository, requested_ref, resolved_commit, snapshot_id, complete, …), `diagnostics` and `evidence_note`. `changes` returns `history_unavailable` when there is no base, and `removal_unconfirmed` (not `removed`) when the target is incomplete. Ancestry is never inferred.

## Action

```yaml
- uses: blackmath88/observstory@<sha>
  with:
    knowledge: .observstory/knowledge.json   # empty (default) = disabled
```

Writes `data/knowledge.json`, `data/knowledge.changes.json` (versus the first parent, regenerated from Git; needs `fetch-depth: 0`) and `knowledge.html`, and adds a *project knowledge* link to the Project Map footer. A knowledge failure is a warning; the Project Map is still written. Whatever is in the output directory is published if the workflow publishes it — set the manifest's `audience` and selection accordingly.

## Not in this slice

Semantic retrieval (Knowledge Lab), extracted/suggested relationships, folder discovery, retained snapshot store beyond files/Git regeneration, MCP transport.
