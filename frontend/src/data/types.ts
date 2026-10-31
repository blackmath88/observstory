/** Types for the fields the UI reads. The full contracts live in `schema/*.json` and are
 *  enforced at runtime by `validate.ts`; these types never widen what the schemas allow. */

export interface Repository {
  full_name: string;
  url?: string | null;
  default_branch?: string;
  visibility?: string;
  description?: string | null;
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
  attention: SceneAttention[];
}

export interface Knowledge {
  schema: "observstory.knowledge/v1";
  title?: string;
  generated_at: string;
  complete: boolean;
  records: unknown[];
}

export interface EventSchedule {
  schema: "observstory.event-schedule/v0";
  title: string;
  timezone: string;
  coding_deadline?: { event_id?: string; at: string; label: string; basis?: string } | null;
  events: { id: string; label: string; start_at: string; precision?: string }[];
}

export type SourceName = "snapshot" | "scene" | "knowledge" | "event";

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

export interface Bundle {
  base: string;
  receivedAt: string;
  snapshot: SourceResult<Snapshot>;
  scene: SourceResult<Scene>;
  knowledge: SourceResult<Knowledge>;
  event: SourceResult<EventSchedule>;
}
