/** Types for the fields the UI reads. The full contracts live in `schema/*.json` and are
 *  enforced at runtime by `validate.ts`; these types never widen what the schemas allow. */

export interface Repository {
  full_name: string;
  url?: string | null;
  default_branch?: string;
  visibility?: string;
  description?: string | null;
}

export interface Issue {
  number: number;
  title: string;
  state: string;
  url?: string | null;
  labels: unknown[];
  updated_at?: string;
}

export interface Snapshot {
  schema: "observstory.snapshot/v1";
  generated_at: string;
  trigger?: { event?: string; run_id?: string; sha?: string } | null;
  repository: Repository;
  window: { hours: number; since: string };
  summary: {
    in_flight: number;
    areas_active: number;
    commits_in_window: number;
    open_issues: number;
    signals: { overlap: number; stale: number; waiting: number; burst: number };
  };
  provenance: { degraded: string[]; observations_fetched_at?: string };
  issues: Issue[];
}

export interface SceneZone {
  id: string;
  label: string;
  description?: string;
  order: number;
  state: "active" | "quiet";
  groups: string[];
  in_flight: number;
  attention: boolean;
  recently_changed: string[];
  recently_changed_more: number;
}

export interface SceneAttention {
  kind: string;
  target: string;
  label: string;
  basis?: string;
  confidence?: string;
}

export interface SceneGroup {
  id: string;
  zone: string;
  path: string;
  label: string;
  attention: boolean;
  nodes: string[];
  also_active: string[];
  recent_commits: number;
  last_activity_at?: string | null;
  age_hours?: number | null;
}

export interface SceneNode {
  id: string;
  kind: "pull_request" | "branch" | "direct" | string;
  group: string;
  zone: string;
  ref: string;
  label: string;
  url?: string | null;
  status: "in_flight" | "draft" | "stale" | "landed" | string;
  review_state?: string | null;
  actors: string[];
  last_activity_at?: string | null;
  age_hours?: number | null;
  also_touches: string[];
  flags: string[];
  attention: boolean;
}

export interface SceneEdge {
  id: string;
  type: "overlap" | "waiting" | string;
  from: string;
  to: string;
  basis?: string;
  confidence?: string;
  areas?: string[];
  files?: string[];
}

/** Declared collaboration state, reconciled with observed work (coordination.py). Loosely typed
 *  in scene-v1 ("object or null"), so every field is read defensively. */
export interface Coordination {
  now?: string;
  next_gate?: string | null;
  hours_to_next?: number | null;
  proposed_pending?: number;
  sessions?: { id: string; kind?: string; label: string; at: string; open_questions?: string[] }[];
  gates?: {
    id: string;
    kind?: string;
    label: string;
    at: string;
    passed?: boolean;
    next?: boolean;
    confirmed_by?: string;
    cue?: string | null;
  }[];
  commitments?: {
    id: string;
    text: string;
    owner?: string | null;
    due?: string | null;
    state?: string;
    confirmed_by?: string;
    cue?: string | null;
  }[];
  decisions?: { id: string; text: string; confirmed_by?: string }[];
  cues?: { id: string; summary?: string }[];
}

export interface Scene {
  schema: "observstory.scene/v1";
  source: {
    generated_at: string;
    repository: string;
    repository_url?: string | null;
    default_branch?: string;
    window_hours: number;
    title?: string | null;
    degraded: string[];
  };
  status: { in_flight: number; overlaps: number; waiting: number; stale: number; areas_active: number };
  zones: SceneZone[];
  groups: SceneGroup[];
  nodes: SceneNode[];
  edges: SceneEdge[];
  attention: SceneAttention[];
  coordination?: Coordination | null;
}

export interface KnowledgeRecord {
  id: string;
  type: string;
  status: string;
  title: string;
  path?: string | null;
  url?: string | null;
  excerpt?: string | null;
  basis?: { kind?: string; declarations?: { path: string; quote?: string; url?: string; line?: number }[] } | null;
}

export interface Knowledge {
  schema: "observstory.knowledge/v1";
  title?: string;
  generated_at: string;
  complete: boolean;
  resolved_commit?: string;
  diagnostics?: unknown[];
  records: KnowledgeRecord[];
  selection?: { current_direction?: { state: string; reason?: string; record?: string | null; candidates?: string[] } };
}

export interface EventSchedule {
  schema: "observstory.event-schedule/v0";
  title: string;
  timezone: string;
  source?: { kind?: string; provided_by?: string; independently_verified?: boolean; note?: string } | null;
  coding_deadline?: { event_id?: string; at: string; label: string; basis?: string; note?: string } | null;
  events: {
    id: string;
    label: string;
    start_at: string;
    end_at?: string | null;
    precision?: string;
    location?: string;
    source_time?: string;
  }[];
}

export interface WorkspaceRecord {
  milestone?: boolean;
  id: string;
  title: string;
  kind: string;
  context?: string;
  status?: string;
  members?: string[];
  sources?: string[];
  attention?: string;
  resume?: { stopping_point: string; next_action: string };
  planned?: { start: string; end?: string; precision: "day" | "month" | "year" };
}
export interface Workspace {
  schema: "observstory.workspace/v1";
  source_commit?: string;
  records: WorkspaceRecord[];
  relations: { from: string; to: string; type: string }[];
}

export type SourceName = "snapshot" | "scene" | "knowledge" | "event" | "workspace";

export interface SourceSpec<T> {
  name: SourceName;
  file: string;
  /** Required inputs block the activity views; optional ones only hide their own panels. */
  required: boolean;
  /** The `schema` value this frontend understands. */
  schemaId: string;
  label: string;
  _type?: T;
}

/** What happened when a source was loaded. Absent data is never turned into zeros. */
export type SourceResult<T> =
  | { status: "ok"; data: T; url: string; contract: "full" | "identity-only" }
  | { status: "missing"; url: string }
  | { status: "unreadable"; url: string; detail: string }
  | { status: "unsupported"; url: string; found: string | null; expected: string }
  | { status: "invalid"; url: string; issues: string[] }
  | { status: "unreachable"; url: string; detail: string };

/** Other pages the same Action run published beside this app (classic map, replay, …). */
export interface CompanionView {
  href: string;
  label: string;
}

export interface Bundle {
  base: string;
  receivedAt: string;
  views: CompanionView[];
  snapshot: SourceResult<Snapshot>;
  scene: SourceResult<Scene>;
  knowledge: SourceResult<Knowledge>;
  event: SourceResult<EventSchedule>;
  workspace: SourceResult<Workspace>;
}
