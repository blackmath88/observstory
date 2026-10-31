import type { Bundle, EventSchedule, Knowledge, Scene, Snapshot, SourceName, SourceResult, SourceSpec } from "./types";
import { isRecord, validate } from "./validate";

export const SOURCES = {
  snapshot: { name: "snapshot", file: "snapshot.json", required: true, schemaId: "observstory.snapshot/v1", label: "Snapshot" },
  scene: { name: "scene", file: "scene.json", required: true, schemaId: "observstory.scene/v1", label: "Scene" },
  knowledge: {
    name: "knowledge",
    file: "knowledge.json",
    required: false,
    schemaId: "observstory.knowledge/v1",
    label: "Project knowledge",
  },
  event: { name: "event", file: "event.json", required: false, schemaId: "observstory.event-schedule/v0", label: "Event schedule" },
} as const satisfies Record<SourceName, SourceSpec<unknown>>;

/** Where the data lives. Production: `./data/` next to index.html (what the Action writes).
 *  A `?data=` query may point elsewhere for review, but only to a relative path on the same
 *  origin; absolute URLs, protocol-relative URLs and parent escapes are refused. */
export function resolveDataBase(search: string, fallback = "./data/"): string {
  const requested = new URLSearchParams(search).get("data");
  if (!requested) return fallback;
  const safe = /^(\.\/)?[A-Za-z0-9._-]+(\/[A-Za-z0-9._-]+)*\/?$/.test(requested) && !requested.split("/").includes("..");
  if (!safe) return fallback;
  return requested.endsWith("/") ? requested : `${requested}/`;
}

type Fetcher = (url: string) => Promise<Response>;

export async function loadSource<T>(spec: SourceSpec<T>, base: string, fetcher: Fetcher): Promise<SourceResult<T>> {
  const url = `${base}${spec.file}`;
  let res: Response;
  try {
    res = await fetcher(url);
  } catch (e) {
    return { status: "unreachable", url, detail: e instanceof Error ? e.message : String(e) };
  }
  if (res.status === 404) return { status: "missing", url };
  if (!res.ok) return { status: "unreachable", url, detail: `HTTP ${res.status}` };
  let data: unknown;
  try {
    data = JSON.parse(await res.text());
  } catch (e) {
    return { status: "unreadable", url, detail: e instanceof Error ? e.message : "not valid JSON" };
  }
  const found = isRecord(data) && typeof data.schema === "string" ? data.schema : null;
  if (found !== spec.schemaId) return { status: "unsupported", url, found, expected: spec.schemaId };
  const v = validate(spec.name, data);
  if (!v.ok) return { status: "invalid", url, issues: v.issues };
  return { status: "ok", data: data as T, url, contract: v.contract };
}

export async function loadBundle(
  base: string,
  fetcher: Fetcher = (u) => fetch(u, { cache: "no-store" }),
  now = new Date(),
): Promise<Bundle> {
  const [snapshot, scene, knowledge, event] = await Promise.all([
    loadSource<Snapshot>(SOURCES.snapshot, base, fetcher),
    loadSource<Scene>(SOURCES.scene, base, fetcher),
    loadSource<Knowledge>(SOURCES.knowledge, base, fetcher),
    loadSource<EventSchedule>(SOURCES.event, base, fetcher),
  ]);
  return { base, receivedAt: now.toISOString(), snapshot, scene, knowledge, event };
}

/** The activity views need both required sources; everything else degrades per panel. */
export function activity(bundle: Bundle): { snapshot: Snapshot; scene: Scene } | null {
  if (bundle.snapshot.status !== "ok" || bundle.scene.status !== "ok") return null;
  return { snapshot: bundle.snapshot.data, scene: bundle.scene.data };
}
