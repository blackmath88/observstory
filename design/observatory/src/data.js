/* SYNTHETIC STUDY DATA — not observed from any repository.
 *
 * Shaped like a subset of observstory.scene/v1 (schema/scene-v1.json) so the
 * study exercises real field names: zones, groups, nodes, edges, attention,
 * details. The project name echoes the BaselHack use case so the content reads
 * plausibly; every item, author handle and commit below is invented.
 *
 * Three states share one project:
 *   quiet   — Sat 10:00, four items in flight, nothing related
 *   overlap — Sat 18:00, an overlap, a waiting dependency, a stale branch,
 *             one declared commitment, and a degraded collection
 *   replay  — repository file history (feed 1 in OBSERVATORY-REWRITE.md);
 *             Observatory state history and graph events are shown as
 *             unavailable, because they are.
 */
(function (root) {
  "use strict";

  const PROJECT = {
    repository: "synthetic/photo-frame-commons",
    title: "Photo Frame Commons",
    notice: "Synthetic study data — invented for design review, not observed from GitHub.",
    window_hours: 48,
    default_branch: "main",
  };

  const ZONES = [
    { id: "intent", label: "Intent", description: "Concept, research index, decisions" },
    { id: "build", label: "Build", description: "Capture, provenance, frame UI" },
    { id: "verify", label: "Verify", description: "Tests and review fixtures" },
    { id: "ship", label: "Ship", description: "Preview and deploy" },
  ];

  const GROUPS = [
    { id: "area:docs/concept", zone: "intent", path: "docs/concept" },
    { id: "area:research/index", zone: "intent", path: "research/index" },
    { id: "area:src/capture", zone: "build", path: "src/capture" },
    { id: "area:src/provenance", zone: "build", path: "src/provenance" },
    { id: "area:src/frame-ui", zone: "build", path: "src/frame-ui" },
    { id: "area:tests", zone: "verify", path: "tests" },
    { id: "area:deploy", zone: "ship", path: "deploy" },
  ];

  const N = (o) => Object.assign({ kind: o.id.startsWith("pr:") ? "pull_request" : "branch", also_touches: [], flags: [], url: null }, o);

  const QUIET = {
    id: "quiet",
    label: "Quiet",
    generated_at: "2026-10-26T10:00:00Z",
    collected: "Sat 26 Oct · 10:00 UTC",
    trigger: "push",
    degraded: [],
    coverage: [
      ["Pull requests", "complete"], ["Branches", "complete"], ["Default-branch commits", "complete"], ["Issues", "complete"],
    ],
    nodes: [
      N({ id: "pr:19", ref: "#19", label: "Concept: the circumstances of a photo", group: "area:docs/concept", status: "draft", age_hours: 3.1, actors: ["mira"] }),
      N({ id: "pr:21", ref: "#21", label: "Provenance record schema", group: "area:src/provenance", status: "in_flight", age_hours: 0.6, actors: ["jonas"] }),
      N({ id: "pr:24", ref: "#24", label: "Frame gallery layout", group: "area:src/frame-ui", status: "in_flight", age_hours: 1.4, actors: ["ada"] }),
      N({ id: "branch:pages-preview", ref: "pages-preview", label: "Pages preview workflow", group: "area:deploy", status: "in_flight", age_hours: 2.2, actors: ["sam"] }),
    ],
    edges: [],
    attention: [],
    commitments: [],
    gates: [
      { label: "Hackathon plan", state: "passed", at: 0.12 },
      { label: "Consent copy reviewed", state: "not_started", at: 0.55 },
      { label: "Demo dry-run", state: "not_started", at: 0.86 },
    ],
    now: 0.38,
  };

  const OVERLAP = {
    id: "overlap",
    label: "Overlap",
    generated_at: "2026-10-26T18:00:00Z",
    collected: "Sat 26 Oct · 18:00 UTC",
    trigger: "pull_request",
    degraded: ["issues skipped: request budget reserved for pull-request files"],
    coverage: [
      ["Pull requests", "complete"], ["Branches", "complete"], ["Default-branch commits", "complete"], ["Issues", "skipped"],
    ],
    nodes: [
      N({ id: "pr:21", ref: "#21", label: "Provenance record schema", group: "area:src/provenance", status: "in_flight", age_hours: 0.4, actors: ["jonas"], also_touches: ["area:tests"], attention: true }),
      N({ id: "pr:22", ref: "#22", label: "Capture consent flow", group: "area:src/capture", status: "in_flight", age_hours: 0.9, actors: ["lea"], also_touches: ["area:src/provenance"], attention: true }),
      N({ id: "branch:voice-notes", ref: "voice-notes", label: "Voice note attachments", group: "area:src/capture", status: "in_flight", age_hours: 1.7, actors: ["noor"], attention: true }),
      N({ id: "pr:24", ref: "#24", label: "Frame gallery layout", group: "area:src/frame-ui", status: "in_flight", age_hours: 2.5, actors: ["ada"] }),
      N({ id: "pr:25", ref: "#25", label: "Provenance round-trip tests", group: "area:tests", status: "in_flight", age_hours: 3.0, actors: ["jonas", "kai"] }),
      N({ id: "pr:19", ref: "#19", label: "Concept: the circumstances of a photo", group: "area:docs/concept", status: "draft", age_hours: 6.2, actors: ["mira"] }),
      N({ id: "pr:26", ref: "#26", label: "Research index: metadata-only manifest", group: "area:research/index", status: "in_flight", age_hours: 4.8, actors: ["ida"] }),
      N({ id: "branch:pages-preview", ref: "pages-preview", label: "Pages preview workflow", group: "area:deploy", status: "stale", age_hours: 74, actors: ["sam"], flags: ["no_pull_request"] }),
    ],
    edges: [
      {
        id: "overlap:pr:21|pr:22", type: "overlap", from: "pr:21", to: "pr:22", directed: false,
        basis: "derived", confidence: "high", areas: ["src/provenance"], files: ["src/provenance/record.py", "src/provenance/__init__.py"],
        rule: "overlap · min_shared_files=1 · window=48h",
        summary: "#21 and #22 both change src/provenance; 2 shared files",
      },
      {
        id: "waiting:branch:voice-notes>pr:22", type: "waiting", from: "branch:voice-notes", to: "pr:22", directed: true,
        basis: "heuristic", confidence: "medium", areas: ["src/capture"], files: [],
        rule: "waiting · marker='waits on #n' in branch head commit",
        summary: "voice-notes says it waits on #22",
        quote: "wip: attachments — waits on #22 for consent state",
      },
    ],
    attention: [
      { kind: "overlap", target: "overlap:pr:21|pr:22", label: "#21 and #22 change src/provenance in parallel", basis: "derived", confidence: "high" },
      { kind: "waiting", target: "waiting:branch:voice-notes>pr:22", label: "voice-notes waits on #22", basis: "heuristic", confidence: "medium" },
      { kind: "stale", target: "branch:pages-preview", label: "pages-preview idle for 3d (no pull request)", basis: "derived", confidence: "high" },
    ],
    gates: [
      { label: "Hackathon plan", state: "passed", at: 0.12 },
      { label: "Consent copy reviewed", state: "in_progress", at: 0.55, linked: "pr:22" },
      { label: "Demo dry-run", state: "not_started", at: 0.86 },
    ],
    now: 0.64,
    commitments: [
      { id: "c1", text: "Consent copy reviewed before demo", declared_by: "lea", state: "open", linked: "pr:22", note: "declared in .observstory/coordination.json · linked work still open" },
    ],
  };

  /* Feed 1 — repository file history. First-parent commits after an explicit
   * baseline. File counts per area are the only reconstructed state. */
  const BASELINE = {
    sha: "4e1c0a2", at: "2026-10-25T09:00:00Z", label: "Baseline: hackathon kickoff commit",
    files: { "docs/concept": 3, "research/index": 1, "src/capture": 2, "src/provenance": 0, "src/frame-ui": 2, "tests": 1, "deploy": 1 },
  };
  const E = (sha, at, area, op, path, msg) => ({ sha, at, area, op, path, msg });
  const EVENTS = [
    E("8b2d1f0", "2026-10-25T09:40Z", "docs/concept", "edit", "docs/concept/brief.md", "Frame the question: whose circumstances travel with a photo"),
    E("c41a9e3", "2026-10-25T10:15Z", "src/provenance", "add", "src/provenance/__init__.py", "Start provenance package"),
    E("1f0e7b2", "2026-10-25T10:16Z", "src/provenance", "add", "src/provenance/record.py", "Draft provenance record"),
    E("77ad310", "2026-10-25T11:02Z", "src/capture", "add", "src/capture/consent.py", "Consent prompt skeleton"),
    E("a90c5d4", "2026-10-25T11:30Z", "research/index", "add", "research/index/manifest.json", "Metadata-only research manifest"),
    E("3e66b81", "2026-10-25T12:10Z", "src/frame-ui", "add", "src/frame-ui/gallery.tsx", "Gallery grid"),
    E("d02f9aa", "2026-10-25T12:45Z", "tests", "add", "tests/test_record.py", "Round-trip test for records"),
    E("5bc7e02", "2026-10-25T13:20Z", "src/capture", "edit", "src/capture/consent.py", "Consent states: asked / given / withdrawn"),
    E("e8d3a11", "2026-10-25T14:05Z", "docs/concept", "add", "docs/concept/voices.md", "Note on voices and attribution"),
    E("6a1f4c7", "2026-10-25T15:30Z", "src/frame-ui", "edit", "src/frame-ui/gallery.tsx", "Caption slot under each frame"),
    E("b3f0d58", "2026-10-25T16:10Z", "deploy", "add", "deploy/pages.yml", "Pages preview workflow"),
    E("0c9e2b6", "2026-10-25T17:40Z", "src/capture", "remove", "src/capture/legacy_upload.py", "Remove legacy upload path"),
    E("f71b3a0", "2026-10-25T19:05Z", "src/provenance", "edit", "src/provenance/record.py", "Record links capture consent"),
    E("29de4f3", "2026-10-25T20:30Z", "tests", "add", "tests/test_consent.py", "Consent withdrawal test"),
    E("9a4c6e1", "2026-10-26T08:50Z", "research/index", "edit", "research/index/manifest.json", "Manifest: add source licence field"),
    E("4d8b0f2", "2026-10-26T09:35Z", "src/frame-ui", "add", "src/frame-ui/frame.tsx", "Single frame view"),
    E("e5a71c9", "2026-10-26T10:20Z", "docs/concept", "remove", "docs/concept/old-pitch.md", "Drop superseded pitch"),
    E("7c30d6b", "2026-10-26T11:45Z", "src/provenance", "add", "src/provenance/export.py", "Export provenance as JSON-LD"),
    E("b81e2a4", "2026-10-26T13:10Z", "tests", "edit", "tests/test_record.py", "Correction: record test used wrong fixture"),
    E("2f6d9c8", "2026-10-26T15:00Z", "src/capture", "add", "src/capture/voice.py", "Voice note capture"),
  ];

  const FEEDS = [
    { id: "files", label: "Repository file history", available: true, detail: "first-parent commits on main after baseline 4e1c0a2 · additions, edits, removals" },
    { id: "state", label: "Observatory state history", available: false, detail: "not available — the current Action is stateless and keeps no past snapshots" },
    { id: "graph", label: "Knowledge graph events", available: false, detail: "not connected — Knowledge Lab adapter is future work" },
  ];

  /* Deterministic reconstruction: same position → same state. */
  function replayAt(pos) {
    const files = Object.assign({}, BASELINE.files);
    const touched = {};
    for (let i = 0; i <= pos && i < EVENTS.length; i++) {
      const e = EVENTS[i];
      if (e.op === "add") files[e.area] = (files[e.area] || 0) + 1;
      if (e.op === "remove") files[e.area] = Math.max(0, (files[e.area] || 0) - 1);
      touched[e.area] = touched[e.area] || { add: 0, edit: 0, remove: 0 };
      touched[e.area][e.op]++;
    }
    return { pos, event: EVENTS[pos] || null, files, touched };
  }

  /* The lasting record of each commit as points per area: baseline files,
   * additions, and removals kept as hollow points (deletions are preserved). */
  function replayDots(pos) {
    const dots = [];
    for (const [area, n] of Object.entries(BASELINE.files)) for (let i = 0; i < n; i++) dots.push({ key: `${area}#base${i}`, area, removed: false });
    for (let i = 0; i <= pos && i < EVENTS.length; i++) {
      const e = EVENTS[i];
      if (e.op === "add") dots.push({ key: e.path, area: e.area, removed: false, fresh: i === pos });
      if (e.op === "remove") {
        const hit = dots.find((d) => d.key === e.path && !d.removed) || [...dots].reverse().find((d) => d.area === e.area && !d.removed && d.key.includes("#base"));
        if (hit) hit.removed = true;
      }
    }
    return dots;
  }

  root.ObsData = { PROJECT, ZONES, GROUPS, STATES: { quiet: QUIET, overlap: OVERLAP }, BASELINE, EVENTS, FEEDS, replayAt, replayDots };
})(typeof window !== "undefined" ? window : globalThis);
