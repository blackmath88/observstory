# Scene grammar (`observstory.scene/v1`)

The Project Map isn't drawn from GitHub data. It's drawn from a **scene**: a small, versioned
visual contract compiled from the typed snapshot.

```text
GitHub → observations.json → snapshot.json → map_compiler.py → scene.json → map_render.py → index.html
                                    (typed state)          (meaning → structure)        (structure → pixels)
```

Contract: [`schema/scene-v1.json`](../../schema/scene-v1.json). Compiler:
[`src/observstory/map_compiler.py`](../../src/observstory/map_compiler.py). The compiler is pure and
deterministic (`tests/test_map.py::Compiler`). The renderer interprets nothing: every word and
every connector on the page comes from the scene.

## Four element types

| Element | Is | Comes from | Key fields |
|---|---|---|---|
| **zone** | a lane, in configured order | `snapshot.lanes` | `order`, `state` (active / quiet), `groups`, `in_flight`, `recently_changed` |
| **group** | an area inside a zone that has something to show | `snapshot.areas` | `path`, `nodes` (drawn here), `also_active` (drawn elsewhere, referenced here), `attention` |
| **node** | a work item, **drawn once** | `snapshot.work_items` | `ref`, `label`, `status` (in_flight / draft / stale / landed), `age_hours`, `also_touches`, `flags` |
| **edge** | a relationship between two nodes | `overlap` and `waiting` signals | `type`, `from`, `to`, `directed`, `basis`, `confidence`, `areas`, `files`, `signals` |

Plus two lists that aren't drawn as shapes:

- **attention**: ordered references (overlap, then waiting, then stale) to the edges or nodes that deserve a conversation. It drives the "Needs attention" column.
- **details**: the evidence payload (signal evidence, file lists, merge bases), shown only when the inspector opens.

The issue proposed `BADGE`, `NOTE` and `BAND` as well. They're left out because nothing in the
snapshot needs them yet: badges are node `flags`, notes are the attention list, and bands would
be time, which is a node field (`age_hours`), not a shape.

## Compile rules

1. **Zones follow the configured lane order.** With no config, the default lanes are used (Intent → Build → Verify → Ship), plus `other` if any path isn't claimed by a lane. A zone with nothing to show is `quiet` and lists up to six areas that changed recently.
2. **What becomes a node.** Every in-flight work item: open PRs, drafts, and branches without a PR (stale items included, marked `stale`). Landed default-branch changes become nodes **only if they take part in a relationship**. Merged and closed work doesn't appear.
3. **Each node is drawn exactly once, in its primary area**: the area where it changes the most files. Ties go to the earlier lane, then the path. Landed nodes are placed in the area of their overlap.
4. **Every area a shown node touches becomes a group.** Where the node isn't drawn, the group lists it in `also_active`, so a lane never looks quiet while work is changing it.
5. **Overlap edges are one per pair of work items.** Every area and shared file the pair has in common is merged into that one edge, so a relationship spanning nine areas is one line, not nine. Waiting edges are directed from the waiting item to the one it waits on.
6. **Order carries meaning, not coordinates.**
   - Groups: attention first, then more nodes, then more references, then most recent.
   - Nodes within a group: most recent first; drafts, landed and stale work sink to the end.
   - Attention list: overlaps by confidence, then waiting, then stale by idle time.
7. **Time is a field, not a position.** `age_hours` is computed from the snapshot's own `generated_at`, so the scene stays deterministic. The renderer shows it as small age labels and as recency order.

## Why an intermediate scene

- The same renderer draws any project shape: 2 lanes or 8, default or custom, one area or forty.
- Layout decisions can be tested without a browser: placement, grouping and ordering are all in the compiler.
- Another renderer (a native app, an image export, a terminal view) could read the same `scene.json`.
